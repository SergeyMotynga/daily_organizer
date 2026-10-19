// PNG всегда строится из окончательного SVG, включая контуры шрифта.
const sharp = require('sharp');
const fs = require('node:fs/promises');
const path = require('node:path');
async function main() {
  const directory = process.argv[2];
  const files = (await fs.readdir(directory)).filter(file => file.endsWith('.svg'));
  let index = 0;
  async function worker() {
    while (index < files.length) {
      const name = files[index++];
      await sharp(path.join(directory, name), {limitInputPixels: false})
        .png().toFile(path.join(directory, name.replace(/\.svg$/, '.png')));
    }
  }
  await Promise.all(Array.from({length: 4}, worker));
  const assets = path.join(directory, '..', 'assets');
  await sharp(path.join(assets, 'route-lockup-light.svg')).resize({width: 900})
    .extend({top: 45, bottom: 45, left: 45, right: 45, background: '#F7F6F3'})
    .flatten({background: '#F7F6F3'}).png().toFile(path.join(assets, 'route-preview.png'));
  process.stdout.write(`Rasterized ${files.length} SVG files\n`);
}
main().catch(error => { process.stderr.write(String(error)); process.exitCode = 1; });
