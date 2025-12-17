// script.js for index.html
const input = document.getElementById('imageInput');
const preview = document.getElementById('preview');
const paletteDiv = document.getElementById('palette');
const extras = document.getElementById('extras');
const topN = document.getElementById('topN');

input && input.addEventListener('change', async (e) => {
  const file = e.target.files[0];
  if (!file) return;
  // preview
  preview.innerHTML = `<img src="${URL.createObjectURL(file)}" alt="preview">`;

  const form = new FormData();
  form.append('image', file);
  if (topN) form.append('top_n', topN.value);

  try {
    const res = await fetch('/upload', { method: 'POST', body: form });
    const data = await res.json();
    if (data.error) {
      alert(data.error);
      return;
    }
    // render palette
    paletteDiv.innerHTML = '';
    data.palette.forEach(c => {
      const d = document.createElement('div');
      d.className = 'color-block';
      d.style.background = c.hex;
      d.innerHTML = `<div>${c.hex}</div>`;
      d.title = `RGB: ${c.rgb.join(', ')} • Comp: ${c.complement_hex}`;
      d.onclick = () => {
        navigator.clipboard.writeText(c.hex);
        d.style.transform = 'scale(0.98)';
        setTimeout(()=>d.style.transform='scale(1)',120);
      };
      paletteDiv.appendChild(d);
    });

    // extras: average + downloads + gradient
    extras.innerHTML = `
      <div style="display:flex;gap:18px;align-items:center;justify-content:center;flex-wrap:wrap">
        <div>
          <div class="small">Average Color</div>
          <div class="avg-box" style="background:${data.average.hex}"></div>
          <div class="small">${data.average.hex}</div>
        </div>
        <div>
          ${data.png_url ? `<a href="${data.png_url}" download><button>Download PNG</button></a>` : ''}
          <a href="${data.json_url}" download><button>Download JSON</button></a>
        </div>
      </div>
    `;
  } catch (err) {
    console.error(err);
    alert('Upload failed: ' + (err.message || err));
  }
});
