// Test: what does require('electron') return inside Electron's runtime?
try {
  const e = require('electron');
  console.log('typeof electron:', typeof e);
  console.log('type:', Object.prototype.toString.call(e));
  if (typeof e === 'object' && e !== null) {
    console.log('keys:', Object.keys(e).join(', '));
  } else {
    console.log('value:', String(e).substring(0, 100));
  }
} catch (err) {
  console.log('require failed:', err.message);
}
