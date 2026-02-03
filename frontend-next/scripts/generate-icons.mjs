import sharp from 'sharp';
import { mkdir, readFile } from 'fs/promises';
import { join, dirname } from 'path';
import { fileURLToPath } from 'url';

const __dirname = dirname(fileURLToPath(import.meta.url));
const rootDir = join(__dirname, '..');
const publicDir = join(rootDir, 'public');
const iconsDir = join(publicDir, 'icons');

// Icon sizes for PWA
const sizes = [72, 96, 128, 144, 152, 192, 384, 512];

async function generateIcons() {
  console.log('Creating icons directory...');
  await mkdir(iconsDir, { recursive: true });

  // Read the actual logo_hoofs.svg
  const logoPath = join(publicDir, 'logo_hoofs.svg');
  const logoSvg = await readFile(logoPath);

  console.log('Generating regular icons from logo_hoofs.svg...');

  // Generate regular icons with background
  for (const size of sizes) {
    const outputPath = join(iconsDir, `icon-${size}.png`);

    // Create a background with the logo centered
    const padding = Math.round(size * 0.1);
    const logoSize = size - (padding * 2);

    // Create background SVG with rounded corners
    const backgroundSvg = `
      <svg width="${size}" height="${size}" xmlns="http://www.w3.org/2000/svg">
        <defs>
          <linearGradient id="bg" x1="0%" y1="0%" x2="100%" y2="100%">
            <stop offset="0%" style="stop-color:#8B7355"/>
            <stop offset="100%" style="stop-color:#6B5344"/>
          </linearGradient>
        </defs>
        <rect width="${size}" height="${size}" rx="${Math.round(size * 0.15)}" fill="url(#bg)"/>
      </svg>
    `;

    // Resize logo and composite onto background
    const resizedLogo = await sharp(logoSvg)
      .resize(logoSize, logoSize, { fit: 'contain', background: { r: 0, g: 0, b: 0, alpha: 0 } })
      .png()
      .toBuffer();

    await sharp(Buffer.from(backgroundSvg))
      .composite([{
        input: resizedLogo,
        top: padding,
        left: padding,
      }])
      .png()
      .toFile(outputPath);

    console.log(`  Created icon-${size}.png`);
  }

  // Generate maskable icons (more padding for safe zone)
  console.log('Generating maskable icons...');
  for (const size of [192, 512]) {
    const outputPath = join(iconsDir, `icon-maskable-${size}.png`);

    // Maskable icons need 20% safe zone on each side
    const padding = Math.round(size * 0.2);
    const logoSize = size - (padding * 2);

    const backgroundSvg = `
      <svg width="${size}" height="${size}" xmlns="http://www.w3.org/2000/svg">
        <defs>
          <linearGradient id="bg" x1="0%" y1="0%" x2="100%" y2="100%">
            <stop offset="0%" style="stop-color:#8B7355"/>
            <stop offset="100%" style="stop-color:#6B5344"/>
          </linearGradient>
        </defs>
        <rect width="${size}" height="${size}" fill="url(#bg)"/>
      </svg>
    `;

    const resizedLogo = await sharp(logoSvg)
      .resize(logoSize, logoSize, { fit: 'contain', background: { r: 0, g: 0, b: 0, alpha: 0 } })
      .png()
      .toBuffer();

    await sharp(Buffer.from(backgroundSvg))
      .composite([{
        input: resizedLogo,
        top: padding,
        left: padding,
      }])
      .png()
      .toFile(outputPath);

    console.log(`  Created icon-maskable-${size}.png`);
  }

  // Generate shortcut icons
  console.log('Generating shortcut icons...');

  const addShortcutSvg = `
    <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 96 96">
      <rect width="96" height="96" rx="16" fill="#8B7355"/>
      <path d="M48 24v48M24 48h48" stroke="#FAF7F2" stroke-width="8" stroke-linecap="round"/>
    </svg>
  `;

  const calendarShortcutSvg = `
    <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 96 96">
      <rect width="96" height="96" rx="16" fill="#8B7355"/>
      <rect x="16" y="24" width="64" height="56" rx="8" fill="none" stroke="#FAF7F2" stroke-width="6"/>
      <path d="M16 40h64" stroke="#FAF7F2" stroke-width="6"/>
      <circle cx="32" cy="56" r="6" fill="#FAF7F2"/>
      <circle cx="48" cy="56" r="6" fill="#FAF7F2"/>
      <circle cx="64" cy="56" r="6" fill="#FAF7F2"/>
      <path d="M32 16v16M64 16v16" stroke="#FAF7F2" stroke-width="6" stroke-linecap="round"/>
    </svg>
  `;

  await sharp(Buffer.from(addShortcutSvg))
    .resize(96, 96)
    .png()
    .toFile(join(iconsDir, 'shortcut-add.png'));
  console.log('  Created shortcut-add.png');

  await sharp(Buffer.from(calendarShortcutSvg))
    .resize(96, 96)
    .png()
    .toFile(join(iconsDir, 'shortcut-calendar.png'));
  console.log('  Created shortcut-calendar.png');

  console.log('\nAll icons generated successfully!');
}

generateIcons().catch(console.error);
