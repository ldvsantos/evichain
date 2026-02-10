// Hook afterPack do electron-builder
// Injeta o ícone correto no executável usando rcedit
const path = require('path');
const { rcedit } = require('rcedit');

exports.default = async function afterPack(context) {
    const exeName = context.packager.appInfo.productFilename + '.exe';
    const exePath = path.join(context.appOutDir, exeName);
    const icoPath = path.resolve(__dirname, 'assets', 'icon.ico');

    console.log('  • [afterPack] Injetando ícone no executável...');
    console.log('    exe:', exePath);
    console.log('    ico:', icoPath);

    await rcedit(exePath, {
        icon: icoPath,
        'version-string': {
            ProductName: 'EviChain Desktop',
            FileDescription: 'EviChain Desktop — Plataforma de Inovação Probatória',
            CompanyName: 'EviChain Team',
            LegalCopyright: 'Copyright © 2026 EviChain Team',
            OriginalFilename: exeName
        }
    });

    console.log('  • [afterPack] ✓ Ícone injetado com sucesso!');
};
