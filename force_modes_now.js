
// Force load custom modes script for VSCode extension
console.log('🚀 FORCING MODE RELOAD...');

// If running in VSCode extension context
if (typeof vscode !== 'undefined') {
    console.log('VSCode context detected, reloading...');
    vscode.commands.executeCommand('workbench.action.reloadWindow');
}

// Browser context fallback
if (typeof window !== 'undefined') {
    console.log('Browser context, forcing reload...');
    window.location.reload(true);
}

// Node.js context
if (typeof process !== 'undefined') {
    console.log('Node.js context detected');
    process.exit(0);
}
        