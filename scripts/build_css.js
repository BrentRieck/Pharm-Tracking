const fs = require('fs');
const path = require('path');
const postcss = require('postcss');
const tailwindcss = require('tailwindcss');
const autoprefixer = require('autoprefixer');

const rootDir = path.resolve(__dirname, '..');
const inputPath = path.join(rootDir, 'assets', 'tailwind.css');
const outputPath = path.join(rootDir, 'static', 'build', 'tailwind.css');
const tailwindConfig = path.join(rootDir, 'tailwind.config.js');

async function build() {
  try {
    const css = fs.readFileSync(inputPath, 'utf8');
    const result = await postcss([
      tailwindcss({ config: tailwindConfig }),
      autoprefixer,
    ]).process(css, {
      from: inputPath,
      to: outputPath,
      map: false,
    });

    await fs.promises.mkdir(path.dirname(outputPath), { recursive: true });
    await fs.promises.writeFile(outputPath, result.css);
    console.log(`Built ${path.relative(rootDir, outputPath)}`);
  } catch (error) {
    console.error('Failed to build Tailwind CSS');
    console.error(error);
    process.exit(1);
  }
}

build();
