#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
3x3 Eyes Mega CD — POC v22: latín 8x8 + fuente japonesa conservada.

Uso (Python 3, solo biblioteca estándar; no necesita otros archivos):
  python3 poc_castellano_v22.py "Track 01.bin" --comprobar
  python3 poc_castellano_v22.py "Track 01.bin"
  python3 poc_castellano_v22.py "Track 01.bin" --restaurar
  python3 poc_castellano_v22.py "Track 01.bin" --solo-fuente

Si existe Track 01.bin.bak, parte de él, como los parches antiguos. Comprueba
_000PRG.DAT y EV00006.DAT contra los originales recibidos; si no coinciden,
ABORTA antes de escribir. Nunca sobrescribe un .bak existente.

Sin .bak, exige que el BIN de entrada contenga esos dos archivos originales,
y crea la copia de seguridad antes de aplicar. Reconstruye el track completo
partiendo del original .bak: no acumula parches anteriores.

Un salto de seis bytes añade la ruta latina al estampador estrecho. 114 bytes
de código en relleno residente y 896 bytes de bitmaps en relleno posterior al
último kanji (F6E3). Los glifos japoneses, mapper original y avance original
no se sustituyen. Texto latino: F810..F87F. Cada dibujo: 8x8, una sola copia.
F9xx queda reservado a las ordenes originales de posicion del cursor.
La v22 corrige esa colision, causa de los recuadros vacios de la v21.
Mantiene la separación original entre líneas y alinea la base del latín con
la japonesa: el bitmap ocupa las filas 7..14 de la celda original de 16 filas.

Por defecto cambia seis bloques (dos ramas de tres NPC) de EV00006 IN-PLACE:
no reubica nada ni modifica punteros o flags. --solo-fuente deja EV00006 intacto.
Recalcula EDC/ECC de los sectores MODE1/2352 modificados.

IMPORTANTE: es una prueba experimental. Las rutinas CPU y el parcheador se han
probado de forma aislada; falta la validación con una partida del juego. Cierra
el emulador, aplica y ARRANCA EN FRÍO. No cargues el state antiguo: repondría
fuente/código/texto viejos en RAM. Usa partida de Backup RAM o partida nueva.
"""
import argparse
import hashlib
import json
import os
from pathlib import Path
import shutil
import struct
import sys
import tempfile

_PAYLOAD = json.loads(r'''{"charset":" !\"#$%&'()*+,-./0123456789:;<=>?@ABCDEFGHIJKLMNOPQRSTUVWXYZ[\\]^_`abcdefghijklmnopqrstuvwxyz{|}~ÁÉÍÓÚÜÑáéíóúüñ¡¿…","font_hex":"00000000000000000010101010100010002828000000000000665a24245a6600081c2a180c2a1c08003132040810264600182428102a241a00080810000000000004081010100804002010080808102000002a1c3e1c2a00000008083e0808000000000000202040000000003e00000000000000000000200002040810204000001c22222222221c000818080808081c001c22020c10223e000c12020c22221c00040c14243e040e003e22201c02221c000c12203c22221c003e220204081010001c22221c22221c001c22221e02221c0000002000000020000020000020204000020408100804020000003e003e000000201008040810200038440408100010001c222e2a2e201e000c1222223e2277003c12121c12123c000c12222020221c0078242222222478007e22223820227e007e222238202070001c22404742221c007722223e222277001c08080808081c000e0404244444380077222438242277007020202022227e0063362a2a222277006722322a262273001c224242424438007c2222223c207000182442424a443a007c22223c242277001c22221844423c007f49490808081c007722222222221c0077222214140808007722222a2a2a140077221408142277007722221408081c003e22040810223e1810101010101018004020100804020018080808080808180008142200000000000000000000003e0010080400000000000038043c44443e006020382422227c000018242020221c0006041c2444443e000018244478423c000e107c10101038000e1222221e021c0060202c32222277000800180808083e040004042444443800602e2428382476001808080808081c0000142a2a22227700006c322222227700001c222222221c00182422223c2020000c1222221e020200005c222420207000001c221804221c0010107c1012120c000077222222261b000077222214140800007722222a2a14000077221c142277007722221e02443800003c240810223e000608081008080600080808080808080030080804080830000000064930000004081c22223e227704087e222238227e04081c080808081c04081c2242424438040877222222221c140077222222221c3e0067322a262273081038043c44443e081038444478423c040800180808083e04081c222222221c040877222222261b140077222222261b3e006c32222222770004000404040404000800081020221c0000000000000054","font_count":112,"stub_hex":"0c400810650000600c4008806400005804400810e74041f9000afc8002800000ffffd1c043e9001c3c3c000710183e3c0003e3006400000e3401024200f00211000f8511e3006400000e34010242000f021100f08511528951cfffd851ceffce43e900044e75024000ffeb404ef90000a4f8","stub_length":114,"stub_labels":{"entry":0,"row":44,"pair":50,"skip_high":68,"skip_low":86,"native":102},"hook_hex":"4ef900028966","original_prg_sha256":"bb8d0ee8fde8854f963226de2b0e8b69dedf1452fd2a20eb195281a3adde1097","patched_prg_sha256":"e4f9dbcb5602e4a909cedadfb0c4b8cb2a158e6816417cc4ed10c642238d93f7","original_ev_sha256":"5209b62a419ced3adc3b313f3faf3aee9e657ebae0bd28eee8f04ec3710aad6d","patched_ev_sha256":"8e80aac45651b3db5865e22a60f4b1d47a5dd0647fa85531ec636c54b64f4c5c","prg_sig_hex":"0000060006003ff80600060007f00e7c1ec636c667866306660c3c3800e00000000000003000300030303018300c300c300630063b061e061e000c000c000000","ev_sig_hex":"003804900550059c07e80848064c08a8062c08cc08f209f20a4a0ab20ab4000970000000000000000000003000000000012d00000101ff010082021602260236","targets":[{"offset":84142,"length":36,"text":"¡Hola! áéíóúüñ","npc":"Viejo, rama sin Ling Ling","expected_hex":"f4f2f50ef1981a3d0a06c5daf155945a14292e354ebfdaf14b19f1b0160129354e2bbfdb","replacement_hex":"f87df838f85ff85cf851f811f810f876f877f878f879f87af87bf87cf810f810f810badb"},{"offset":84178,"length":40,"text":"¡Hola! áéíóúüñ","npc":"Viejo, rama con Ling Ling","expected_hex":"f516f517c5daf2fff141bef2250a0319917a0627f5423213f18208192ddaf113100728354e15bfdb","replacement_hex":"f87df838f85ff85cf851f811f810f876f877f878f879f87af87bf87cf810f810f810f810f810badb"},{"offset":85142,"length":23,"text":"ÁÉÍÓÚÜÑ ¿z?","npc":"Bromista, rama sin Ling Ling","expected_hex":"f4f2f50ef1981af123f412f19826bef1b3f1d9cdcdbfdb","replacement_hex":"f86ff870f871f872f873f874f875f810f87ef86af82fdb"},{"offset":85166,"length":36,"text":"ÁÉÍÓÚÜÑ ¿z?","npc":"Bromista, rama con Ling Ling","expected_hex":"f12419f1282df140f12823f37b2a13f1dc08152e13da420324231506150624292c18bfdb","replacement_hex":"f86ff870f871f872f873f874f875f810f87ef86af82ff810f810f810f810f810f810badb"},{"offset":85800,"length":27,"text":"0123456789 +-","npc":"Chica, rama con Ling Ling","expected_hex":"f128f31214f147f20119291242bedaf520f2271d26030a0f5151db","replacement_hex":"f820f821f822f823f824f825f826f827f828f829f810f81bf81ddb"},{"offset":85828,"length":105,"text":"ABCDEFGHIJKLMNOPQRSTUVWXYZ\nabcdefghijklmnopqrstuvwxy","npc":"Chica, rama sin Ling Ling","expected_hex":"f128f31214f147f20119291242bedaf520f2271d26030a0f5151dc0a19f13c19f128f3371a202e15f2acf10b390627daf1ef0c06092a3ef35436f1c90413082a292cbfda39093df182073b1f4d10f196161adaf33af163f1cbf3083cf1ef0d0a1423f137f1ac26bfdb","replacement_hex":"f831f832f833f834f835f836f837f838f839f83af83bf83cf83df83ef83ff840f841f842f843f844f845f846f847f848f849f84adaf851f852f853f854f855f856f857f858f859f85af85bf85cf85df85ef85ff860f861f862f863f864f865f866f867f868f869badb"}]}''')
CHARSET = _PAYLOAD['charset']
FONT = bytes.fromhex(_PAYLOAD['font_hex'])
STUB = bytes.fromhex(_PAYLOAD['stub_hex'])
HOOK = bytes.fromhex(_PAYLOAD['hook_hex'])
PRG_LEN = 327680
EV_LEN = 131072
RAW_SIZE = 2352
DATA_SIZE = 2048
DATA_OFFSET = 16
SYNC = b'\x00' + b'\xFF' * 10 + b'\x00'


class PatchError(Exception):
    pass


def sha256(data):
    return hashlib.sha256(data).hexdigest()


def codificar_es(texto):
    """Texto Unicode -> F810..F87F. \n=salto DA; \f=página DC. Sin DB final.

    No reutiliza la tabla ES antigua ni sustituye glifos japoneses.
    Los caracteres no incluidos en la fuente generan un error explícito.
    """
    out = bytearray()
    for ch in texto:
        if ch == '\n':
            out.append(0xDA)
        elif ch == '\f':
            out.append(0xDC)
        else:
            try:
                n = CHARSET.index(ch)
            except ValueError:
                raise PatchError('Caracter sin glifo v22: %r (U+%04X)' % (ch, ord(ch)))
            out.extend((0xF8, 0x10 + n))
    return bytes(out)


def comprobar_sector(raw, lba):
    if len(raw) != RAW_SIZE or raw[:12] != SYNC or raw[15] != 1:
        raise PatchError('Sector LBA %d no es MODE1/2352. No modifico esta imagen.' % lba)


def comprobar_formato(path):
    size = path.stat().st_size
    if size < RAW_SIZE or size % RAW_SIZE:
        raise PatchError('%s no tiene un tamano valido para MODE1/2352.' % path.name)
    with path.open('rb') as f:
        comprobar_sector(f.read(RAW_SIZE), 0)
    return size


def leer_logico(f, lba0, rel, length):
    """Lee datos ISO de un archivo localizado por LBA, saltando headers/ECC."""
    out = bytearray()
    while length:
        sector_rel, within = divmod(rel, DATA_SIZE)
        lba = lba0 + sector_rel
        f.seek(lba * RAW_SIZE)
        raw = f.read(RAW_SIZE)
        comprobar_sector(raw, lba)
        count = min(length, DATA_SIZE - within)
        out.extend(raw[DATA_OFFSET + within:DATA_OFFSET + within + count])
        length -= count
        rel += count
    return bytes(out)


def buscar_huellas(path, needles):
    """Escaneo en streaming: no carga los 310 MB del track en RAM."""
    found = {name: [] for name in needles}
    overlap = max(len(n) for n in needles.values()) - 1
    tail, absolute, seen = b'', 0, {name: set() for name in needles}
    with path.open('rb') as f:
        while True:
            block = f.read(4 * 1024 * 1024)
            if not block:
                break
            buf = tail + block
            start = absolute - len(tail)
            for name, needle in needles.items():
                pos = buf.find(needle)
                while pos != -1:
                    rawpos = start + pos
                    if rawpos not in seen[name]:
                        seen[name].add(rawpos)
                        found[name].append(rawpos)
                    if len(found[name]) > 128:
                        raise PatchError('Demasiadas coincidencias de ' + name + '; aborto.')
                    pos = buf.find(needle, pos + 1)
            absolute += len(block)
            tail = buf[-overlap:] if overlap else b''
    return found


def localizar_original(path, size):
    needles = {
        '_000PRG': bytes.fromhex(_PAYLOAD['prg_sig_hex']),
        'EV00006': bytes.fromhex(_PAYLOAD['ev_sig_hex']),
    }
    specs = {
        '_000PRG': (0x29020, PRG_LEN, _PAYLOAD['original_prg_sha256']),
        'EV00006': (0xC800, EV_LEN, _PAYLOAD['original_ev_sha256']),
    }
    matches = buscar_huellas(path, needles)
    result = {}
    with path.open('rb') as f:
        for name, (rel_sig, length, expected) in specs.items():
            candidates = []
            for rawpos in matches[name]:
                sector_fp, off_fp = divmod(rawpos, RAW_SIZE)
                if off_fp != DATA_OFFSET + rel_sig % DATA_SIZE:
                    continue
                lba = sector_fp - rel_sig // DATA_SIZE
                if lba < 0 or (lba + (length + DATA_SIZE - 1)//DATA_SIZE) * RAW_SIZE > size:
                    continue
                data = leer_logico(f, lba, 0, length)
                if sha256(data) == expected:
                    candidates.append((lba, data))
            if len(candidates) != 1:
                raise PatchError(
                    '%s: %d copias originales verificadas (se exige 1).\n'
                    'El origen no es compatible o ya esta parcheado. No he cambiado nada.\n'
                    'Necesito un .bak original compatible, o un BIN limpio en otra carpeta.'
                    % (name, len(candidates)))
            result[name] = candidates[0]
    return result


def preparar_archivos(original, solo_fuente=False):
    prg = bytearray(original['_000PRG'][1])
    ev = bytearray(original['EV00006'][1])
    # Guards adicionales, además de los SHA256 completos del origen.
    if prg[0x32F2:0x32F8] != bytes.fromhex('024000ffeb40'):
        raise PatchError('El estampador original no coincide.')
    if prg[0x21766:0x21800] != b'\xFF' * 154:
        raise PatchError('El hueco del stub no esta libre.')
    if prg[0x36C80:0x37000] != b'\x00' * 384 + b'\xFF' * 512:
        raise PatchError('El relleno posterior a la fuente no coincide.')
    if len(STUB) != 114 or len(FONT) != 896 or len(CHARSET) != 112:
        raise PatchError('Payload interno corrupto.')
    changes = [
        ('_000PRG', 0x32F2, HOOK),
        ('_000PRG', 0x21766, STUB),
        ('_000PRG', 0x36C80, FONT),
    ]
    for name, rel, data in changes:
        prg[rel:rel+len(data)] = data
    if prg[0x29000:0x36C80] != original['_000PRG'][1][0x29000:0x36C80]:
        raise PatchError('Se ha alterado un glifo original: aborto.')
    if not solo_fuente:
        for t in _PAYLOAD['targets']:
            off, length = t['offset'], t['length']
            if ev[off:off+length] != bytes.fromhex(t['expected_hex']):
                raise PatchError('Bloque original EV00006 0x%X inesperado.' % off)
            data = bytes.fromhex(t['replacement_hex'])
            if len(data) != length:
                raise PatchError('Longitud de bloque cambiada: aborto.')
            ev[off:off+length] = data
            changes.append(('EV00006', off, data))
    if sha256(prg) != _PAYLOAD['patched_prg_sha256']:
        raise PatchError('SHA256 del programa reconstruido incorrecto.')
    expected_ev = _PAYLOAD['original_ev_sha256'] if solo_fuente else _PAYLOAD['patched_ev_sha256']
    if sha256(ev) != expected_ev:
        raise PatchError('SHA256 del EV reconstruido incorrecto.')
    return changes, bytes(prg), bytes(ev)


# CD-ROM MODE1: EDC (CRC) y paridad P/Q de Reed-Solomon.
def crear_tablas():
    edc, forward, backward = [], [0]*256, [0]*256
    for i in range(256):
        x = i
        for _ in range(8):
            x = (x >> 1) ^ (0xD8018001 if x & 1 else 0)
        edc.append(x)
        x = (i << 1) ^ (0x11D if i & 0x80 else 0)
        forward[i] = x
        backward[i ^ x] = i
    return edc, forward, backward


EDC_LUT, ECC_F, ECC_B = crear_tablas()


def calcular_edc(data):
    edc = 0
    for value in data:
        edc = (edc >> 8) ^ EDC_LUT[(edc ^ value) & 0xFF]
    return edc


def calcular_ecc(src, major_count, minor_count, major_mult, minor_inc):
    size = major_count * minor_count
    if len(src) != size:
        raise PatchError('Longitud interna ECC incorrecta.')
    out = bytearray(major_count * 2)
    for major in range(major_count):
        index = (major >> 1) * major_mult + (major & 1)
        a = b = 0
        for _ in range(minor_count):
            value = src[index]
            index = (index + minor_inc) % size
            a ^= value
            b ^= value
            a = ECC_F[a]
        a = ECC_B[ECC_F[a] ^ b]
        out[major] = a
        out[major + major_count] = a ^ b
    return bytes(out)


def rehacer_edc_ecc(raw):
    sector = bytearray(raw)
    sector[2064:2068] = struct.pack('<I', calcular_edc(sector[:2064]))
    sector[2068:2076] = b'\x00' * 8
    sector[2076:2248] = calcular_ecc(sector[12:2076], 86, 24, 2, 86)
    sector[2248:2352] = calcular_ecc(sector[12:2248], 52, 43, 86, 88)
    return bytes(sector)


def preparar_sectores(source, original, changes):
    sectors = {}
    with source.open('rb') as f:
        for name, rel, data in changes:
            lba0 = original[name][0]
            consumed = 0
            while consumed < len(data):
                sector_rel, within = divmod(rel + consumed, DATA_SIZE)
                lba = lba0 + sector_rel
                if lba not in sectors:
                    f.seek(lba * RAW_SIZE)
                    raw = f.read(RAW_SIZE)
                    comprobar_sector(raw, lba)
                    sectors[lba] = bytearray(raw)
                count = min(len(data) - consumed, DATA_SIZE - within)
                pos = DATA_OFFSET + within
                sectors[lba][pos:pos+count] = data[consumed:consumed+count]
                consumed += count
    return {lba: rehacer_edc_ecc(raw) for lba, raw in sectors.items()}


def verificar_resultado(path, original, expected_prg, expected_ev, sectors=None):
    with path.open('rb') as f:
        if leer_logico(f, original['_000PRG'][0], 0, PRG_LEN) != expected_prg:
            raise PatchError('La verificacion de _000PRG en la salida ha fallado.')
        if leer_logico(f, original['EV00006'][0], 0, EV_LEN) != expected_ev:
            raise PatchError('La verificacion de EV00006 en la salida ha fallado.')
        for lba, expected in (sectors or {}).items():
            f.seek(lba * RAW_SIZE)
            if f.read(RAW_SIZE) != expected:
                raise PatchError('El sector de salida %d no coincide.' % lba)


def reserva_espacio(track, size, copies):
    free = shutil.disk_usage(str(track.parent)).free
    required = copies * size + 16 * 1024 * 1024
    if free < required:
        raise PatchError('No hay espacio libre suficiente: necesito unos %.0f MB temporales.'
                         % (required / (1024 * 1024)))


def copia_backup(track, bak):
    """Creación exclusiva: jamás pisa un backup existente."""
    created = False
    try:
        with bak.open('xb') as out:
            created = True
            with track.open('rb') as src:
                shutil.copyfileobj(src, out, 1024 * 1024)
            out.flush()
            os.fsync(out.fileno())
        shutil.copystat(str(track), str(bak))
    except BaseException:
        if created:
            try:
                bak.unlink()
            except OSError:
                pass
        raise


def escribir_atomico(source, track, size, original, expected_prg, expected_ev, sectors):
    """Escribe a temporal, verifica y solo entonces sustituye el BIN."""
    handle, name = tempfile.mkstemp(prefix=track.name+'.v22-', suffix='.tmp', dir=str(track.parent))
    os.close(handle)
    tmp = Path(name)
    try:
        shutil.copyfile(str(source), str(tmp))
        with tmp.open('r+b') as f:
            for lba, data in sorted(sectors.items()):
                f.seek(lba * RAW_SIZE)
                f.write(data)
            f.flush()
            os.fsync(f.fileno())
        if tmp.stat().st_size != size:
            raise PatchError('El tamano del BIN ha cambiado: aborto.')
        verificar_resultado(tmp, original, expected_prg, expected_ev, sectors)
        shutil.copymode(str(track), str(tmp))
        os.replace(str(tmp), str(track))
    finally:
        if tmp.exists():
            tmp.unlink()


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument('bin', help='Track 01 .bin MODE1/2352')
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument('--comprobar', action='store_true', help='verifica y muestra el plan; no escribe nada')
    mode.add_argument('--restaurar', action='store_true', help='restaura exactamente el .bak original verificado')
    parser.add_argument('--solo-fuente', action='store_true', help='añade el motor/fuente; no cambia dialogos')
    args = parser.parse_args(argv)
    if args.solo_fuente and args.restaurar:
        parser.error('--solo-fuente y --restaurar son incompatibles')
    track = Path(args.bin).expanduser().resolve()
    bak = Path(str(track)+'.bak')
    if not track.is_file():
        raise PatchError('No existe el BIN: ' + str(track))
    size = comprobar_formato(track)
    if args.restaurar and not bak.is_file():
        raise PatchError('No existe ' + bak.name + '. No puedo restaurar sin el backup.')
    source = bak if bak.is_file() else track
    if comprobar_formato(source) != size:
        raise PatchError('El .bak y el BIN no tienen el mismo tamano.')
    print('=== 3x3 Eyes: POC v22 — latín 8x8 + japonés conservado ===')
    print('Track: %d bytes (%d sectores MODE1/2352)' % (size, size//RAW_SIZE))
    print('Origen: ' + source.name)
    print('Localizando y verificando los archivos originales...')
    original = localizar_original(source, size)
    print('VERIFICADO: _000PRG.DAT y EV00006.DAT originales (SHA256 completos).')
    print('LBA _000PRG=%d | EV00006=%d' % (original['_000PRG'][0], original['EV00006'][0]))
    if args.restaurar:
        reserva_espacio(track, size, 1)
        escribir_atomico(source, track, size, original,
                         original['_000PRG'][1], original['EV00006'][1], {})
        print('RESTAURADO exactamente desde ' + bak.name)
        return 0
    changes, expected_prg, expected_ev = preparar_archivos(original, args.solo_fuente)
    sectors = preparar_sectores(source, original, changes)
    print('Fuente adicional: 112 glifos, 8x8 reales, avance horizontal 8 px.')
    print('Glifos japoneses originales: intactos. Interlineado original: intacto.')
    print('Sectores modificados: %d; EDC/ECC recalculados.' % len(sectors))
    if args.solo_fuente:
        print('Modo solo fuente: EV00006 sigue en japones.')
    else:
        print('Textos de prueba: tres NPC, ambas ramas; sin reubicacion ni cambios de flags.')
    current_ok = False
    try:
        verificar_resultado(track, original, expected_prg, expected_ev)
        current_ok = True
    except PatchError:
        pass
    if current_ok:
        print('El contenido del programa/EV ya coincide con esta variante v22.')
    if args.comprobar:
        print('COMPROBACION COMPLETADA. No se ha escrito nada ni creado un backup.')
        return 0
    reserva_espacio(track, size, 1 if bak.is_file() else 2)
    if not bak.is_file():
        print('Creando backup original: ' + bak.name)
        copia_backup(track, bak)
        source = bak
    print('Escribiendo a temporal y verificando antes de sustituir el BIN...')
    escribir_atomico(source, track, size, original, expected_prg, expected_ev, sectors)
    print('V22 APLICADA Y VERIFICADA. Tamano del track sin cambios.')
    print('Backup conservado: ' + bak.name)
    print('ARRANCA EN FRIO. No cargues el state antiguo.')
    print('Para deshacer: python3 poc_castellano_v22.py "%s" --restaurar' % track.name)
    return 0


if __name__ == '__main__':
    try:
        sys.exit(main())
    except (PatchError, OSError) as exc:
        print('\nERROR: %s\nEl BIN no se ha sustituido.' % exc, file=sys.stderr)
        sys.exit(1)
    except KeyboardInterrupt:
        print('\nInterrumpido. Si no se completo la sustitucion, el BIN permanece intacto.', file=sys.stderr)
        sys.exit(130)
