/**
 * SeferFlow Plugin
 */

// Global variable to avoid require errors
var sefeferflowPlugin = {};
var app = null;

console.log("[SeferFlow] Plugin loaded v1.0.0");

function sfLogin() {
  console.log("[SeferFlow] Login button clicked");
  // In real plugin this would show auth form
}

window.sefeferflow = { sfLogin };
