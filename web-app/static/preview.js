const input = document.getElementById("image");
const preview = document.getElementById("preview");

if (input && preview) {
  input.addEventListener("change", () => {
    const file = input.files && input.files[0];
    if (!file) {
      preview.hidden = true;
      preview.removeAttribute("src");
      return;
    }
    preview.src = URL.createObjectURL(file);
    preview.alt = "Selected photo preview";
    preview.hidden = false;
  });
}