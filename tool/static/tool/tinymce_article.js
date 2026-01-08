document.addEventListener("DOMContentLoaded", () => {
    if (!window.tinymce) return;
    const textarea = document.getElementById("id_body");
    if (!textarea) return;
    window.tinymce.init({
        selector: "#id_body",
        menubar: false,
        statusbar: true,
        plugins: "link lists autoresize",
        toolbar: "undo redo | bold italic underline | bullist numlist | blockquote | link | removeformat",
        autoresize_bottom_margin: 16,
        min_height: 640,
        height: 640,
    });
});
