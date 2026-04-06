/**
 * SeferFlow Plugin
 */

if (typeof obsidian !== "undefined") {
  const obsidian = window.PluginAPI.app;
  
  const sefeferflowPlugin = {
    id: "sefeferflow",
    name: "SeferFlow - Audiobook Player",
    manifest: require("./manifest.json")
  };
  
  // Simple version
  console.log("[SeferFlow] Loaded v1.0.0");
  
  // Activate
  if (obsidian && obsidian.plugins) {
    const container = document.createElement("div");
    container.id = "sf-settings";
    container.innerHTML = `
      <h3>🔐 SeferFlow</h3>
      <button id="sf-login" onclick="sfLogin()">Log In</button>
      <div id="sf-status">Click to login</div>
    `;
    
    container.querySelectorAll("button").forEach(btn => {
      btn.addEventListener("click", () => {
        const email = document.getElementById("sf-email").value;
        const pass = document.getElementById("sf-password").value;
        console.log("[SeferFlow] Email:", email, "Pass:", pass);
      });
    });
    
    console.log("[SeferFlow] Created container");
  }
}
