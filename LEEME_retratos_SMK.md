# SMK Horizonte — corrección del parpadeo de retratos al terminar

## Entregables

- **`SMK_Horizontee_fix_retratos_v1.sfc`**: ROM corregida, lista para cargar. Sigue teniendo 1 MiB, sin cabecera de copiador.
- **`arreglar_retratos_smk_horizonte.py`**: alternativa autónoma para parchear tu ROM original local, con `.bak`, comprobación SHA256, escritura atómica y restauración.

No necesitas aplicar el script a la ROM ya corregida. Elige una de las dos opciones.

## Resultado comprobado

Se cargaron tu ROM y tu state en **bsnes 115, formato de state 115.1**, mediante un frontend libretro local. Se reprodujo el defecto de llegada: el primer retrato y su número permanecían tres fotogramas en la posición superior antigua antes de pasar a la fila correcta.

Con la corrección:

- El retrato y el número aparecen directamente en la fila correcta.
- Al comparar **360 fotogramas** desde el state, solo cambian los tres fotogramas defectuosos: 15, 16 y 17 de esta captura. Todos los demás son idénticos píxel a píxel.
- La inspección OAM confirma que ambos sprites están en la fila correcta desde su activación.
- **900 fotogramas de arranque limpio**, con entrada de menú, fueron idénticos entre ambas ROMs.
- El parcheador pasó comprobación sin escritura, aplicación, idempotencia, restauración exacta, rechazo de archivos incompatibles y validación del checksum.

Esto valida la secuencia proporcionada y la prueba de arranque; no equivale a una partida completa por todas las pistas, personajes o modos.

## Uso de la ROM corregida

Cierra el contenido actual y abre `SMK_Horizontee_fix_retratos_v1.sfc` con bsnes.

**Puedes usar el state que has facilitado para reproducir la llegada con la ROM corregida.** En esta prueba el código reparado está en la ROM, no es código antiguo repuesto en RAM como en el caso anterior de Mega CD. Esa combinación ROM nueva + state original se ha probado directamente.

Si RetroArch asocia los estados por nombre de archivo, selecciona/copia el state de prueba para el nombre del contenido corregido según tu configuración. No hace falta modificar su contenido.

Conserva aparte la ROM original. Esta entrega no modifica tus archivos de guardado.

## Alternativa: aplicar el script

Python 3, solo biblioteca estándar. Sustituye el nombre/ruta del ejemplo por tu archivo local. En Windows puedes usar `python` en lugar de `python3`.

Comprobar, sin escribir ni crear backup:

```bash
python3 arreglar_retratos_smk_horizonte.py "SMK_Horizontee.sfc" --comprobar
```

Aplicar:

```bash
python3 arreglar_retratos_smk_horizonte.py "SMK_Horizontee.sfc"
```

Restaurar exactamente el original:

```bash
python3 arreglar_retratos_smk_horizonte.py "SMK_Horizontee.sfc" --restaurar
```

El script acepta solo la ROM original recibida. No sobrescribe un `.bak` existente; si existe, exige que sea ese original y reconstruye desde él. No acumula otros parches que tenga el archivo actual. Un backup incompatible hace que aborte antes de escribir.

## Causa técnica

La ROM ya contiene una rutina de recolocación de OAM en **CPU `$88:9400`, offset de archivo `0x89400`**. Antes de mover las cuatro filas comprueba el tile del número 1, la posición Y antigua y el byte de atributos del sprite.

El problema es que compara los atributos con **`$3D` exacto**. Ese byte incluye la paleta. Durante el parpadeo del número, los atributos pasan por `$33`, `$3B`, `$3D`, etc. La posición solo se corregía al llegar al color correspondiente a `$3D`: por eso se veían tres fotogramas del grupo superior.

Se ha cambiado esa comprobación a:

```text
LDA $7E0207
AND #$F1
CMP #$31
BNE siguiente_comprobacion
```

La máscara elimina únicamente los tres bits de paleta. Conserva las comprobaciones de banco de tiles, prioridad y flips. El tile y la posición Y también siguen comprobándose. La segunda parte de la rutina permanece funcionalmente igual.

La rutina crece dos bytes, de 128 a 130, usando dos bytes de relleno comprobados. Se ajusta el primer salto relativo. Se recalculan checksum y complemento SNES; la ROM no cambia de tamaño.

## Hashes

ROM original:

```text
105738925b047e7656f2f92a493f099836f5f8ed098c7d54e7f2f676c3c32ca3
```

ROM corregida:

```text
5a6cfabe3fc1ee522aa3595284402076c5ccbb3329c2207dd84fb0492abf5dac
```

Checksum SNES nuevo: `$ECD0`, complemento `$132F`.
