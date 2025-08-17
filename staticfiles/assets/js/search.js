document.addEventListener("DOMContentLoaded", function () {
  const input = document.querySelector('form[action$="/search/"] input[name="q"]');
  if (!input) return;

  let timer = null, box = null;

  function ensureBox() {
    if (box) return box;
    box = document.createElement("div");
    box.className = "position-absolute bg-white border rounded w-100 mt-1 p-2";
    box.style.zIndex = 1050;
    input.parentElement.style.position = "relative";
    input.parentElement.appendChild(box);
    return box;
  }

  input.addEventListener("input", function () {
    const q = input.value.trim();
    if (timer) clearTimeout(timer);
    if (!q) { if (box) box.innerHTML = ""; return; }

    timer = setTimeout(async () => {
      const res = await fetch(`/search/suggest/?q=${encodeURIComponent(q)}`);
      const data = await res.json();
      const b = ensureBox();
      if (!data.items.length) { b.innerHTML = ""; return; }
      b.innerHTML = data.items.map(it =>
        `<a class="d-flex align-items-center gap-2 text-decoration-none p-1 rounded hover-bg"
            href="${it.url}">
           ${it.image ? `<img src="${it.image}" alt="" width="36" height="36" style="object-fit:cover;border-radius:4px;">` : ""}
           <span class="small flex-grow-1">${it.title}</span>
           ${it.price ? `<span class="small fw-semibold">₹${it.price}</span>` : ""}
         </a>`
      ).join("");
    }, 200);
  });

  document.addEventListener("click", (e) => {
    if (box && !box.contains(e.target) && e.target !== input) box.innerHTML = "";
  });
});
