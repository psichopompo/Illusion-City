#!/usr/bin/env python3
"""parchea_cast_bin.py - parchea un [CAST].bin EN SITIO, sin reconstruir nada.

Por que asi: el .bin de trabajo ya lleva TODA la traduccion (167 ficheros
parcheados in situ por el pipeline del otro chat). Reescribir la ISO desde cero
obliga a regenerar cabeceras de sector y paridades EDC/ECC y puede dejar cosas
desplazadas. Tocando el .bin en su sitio, todo lo demas queda byte a byte igual.

Uso:
    python3 tools/parchea_cast_bin.py ENTRADA.bin                 # solo diagnostico
    python3 tools/parchea_cast_bin.py ENTRADA.bin SALIDA.bin      # aplica el parche

Que hace:
 1. Comprueba la estructura (2352 B/sector, sync, modo 1, MSF).
 2. Extrae la region de START.BIN (LBA 59, 98184 B) con el mapeo por sectores
    y la compara con `recursos/del_state/START_correcto.bin` (el START del build
    bueno, extraido del savestate). Deben ser IDENTICOS: eso prueba que el .bin
    de entrada es el mismo build que el state.
 3. Aplica el candidato de anchura de la caja: file 0x11B55 ($08 del descriptor
    del menu, $A423A): 26 -> 28 unidades.
 4. Vuelca el resultado.
"""
import hashlib
import os
import struct
import sys

AQUI = os.path.dirname(os.path.abspath(__file__))
REC = os.path.dirname(AQUI)
REF = os.path.join(REC, 'del_state', 'START_correcto.bin')

SECTOR = 2352
LBA_START = 59
SZ_START = 98184
OFF_FIX = 0x11B55          # $08 del descriptor del menu (inmediato bajo)
VAL_ANTES = 26
VAL_DESPUES = 28


def extrae_region(raw, lba, size):
    """Extrae `size` bytes del fichero que empieza en LBA, con el mapeo por
    sectores: (LBA + off//2048)*2352 + 16 + off%2048."""
    out = bytearray()
    sectores = (size + 2047) // 2048
    for k in range(sectores):
        out += raw[(lba + k) * SECTOR + 16:(lba + k) * SECTOR + 16 + 2048]
    return bytes(out[:size])


def escribe_region(raw, lba, datos):
    """Escribe `datos` dentro del .bin respetando el mapeo por sectores."""
    for k in range(0, len(datos), 2048):
        trozo = datos[k:k + 2048]
        base = (lba + k // 2048) * SECTOR + 16
        raw[base:base + len(trozo)] = trozo


def main():
    if len(sys.argv) < 2:
        print(__doc__)
        return
    entrada = sys.argv[1]
    salida = sys.argv[2] if len(sys.argv) > 2 else None
    raw = bytearray(open(entrada, 'rb').read())
    print('entrada: %s  (%d B = %d sectores)' % (entrada, len(raw), len(raw) // SECTOR))
    assert len(raw) % SECTOR == 0, 'el fichero no es multiplo de 2352'
    # estructura
    for k in (0, 1, LBA_START):
        sec = raw[k * SECTOR:(k + 1) * SECTOR]
        print('  sector %-5d sync=%s modo=%d msf=%s'
              % (k, sec[:12].hex(' ')[:8] + '..', sec[15], sec[12:15].hex(' ')))
    # el START del .bin contra el del state
    start = extrae_region(raw, LBA_START, SZ_START)
    print()
    print('START.BIN del .bin : MD5 %s' % hashlib.md5(start).hexdigest())
    if os.path.exists(REF):
        ref = open(REF, 'rb').read()
        print('START del state    : MD5 %s' % hashlib.md5(ref).hexdigest())
        dif = [i for i in range(min(len(ref), len(start))) if ref[i] != start[i]]
        if not dif:
            print('  => IDENTICOS: el .bin es del mismo build que el state.')
        else:
            print('  => %d bytes distintos; primeras zonas: %s'
                  % (len(dif), ['0x%X' % x for x in dif[:10]]))
            for off in dif[:6]:
                print('     0x%05X  state=%02X  bin=%02X' % (off, ref[off], start[off]))
    else:
        print('  (no tengo START_correcto.bin para comparar)')
    # el parche
    val = start[OFF_FIX]
    print()
    print('candidato de anchura en file 0x%X: $%02X (%d unidades)' % (OFF_FIX, val, val))
    if val == VAL_ANTES:
        print('  -> sin aplicar. Se aplicaria $%02X (%d unidades = %d px de fila)'
              % (VAL_DESPUES, VAL_DESPUES, VAL_DESPUES * 8))
    elif val == VAL_DESPUES:
        print('  -> ya aplicado')
    else:
        print('  -> VALOR INESPERADO: no toco nada')
        return
    if salida and val == VAL_ANTES:
        start2 = bytearray(start)
        start2[OFF_FIX] = VAL_DESPUES
        escribe_region(raw, LBA_START, bytes(start2))
        open(salida, 'wb').write(bytes(raw))
        print()
        print('escrito %s (%d B)' % (salida, len(raw)))
        print('  MD5 %s' % hashlib.md5(bytes(raw)).hexdigest())
        # reverificar leyendo del fichero escrito
        raw2 = open(salida, 'rb').read()
        st2 = extrae_region(raw2, LBA_START, SZ_START)
        print('  verificado dentro del .bin: file 0x%X = $%02X' % (OFF_FIX, st2[OFF_FIX]))
        iguales = sum(1 for i in range(len(raw)) if raw[i] != raw2[i])
        print('  bytes cambiados en el fichero entero: %d' % iguales)


if __name__ == '__main__':
    main()
