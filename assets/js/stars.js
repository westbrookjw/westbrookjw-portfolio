const canvas = document.getElementById('stars-canvas');
  const ctx = canvas.getContext('2d');

  let stars = [];
  let w, h;

  function resizeCanvas() {
    w = canvas.width = window.innerWidth;
    h = canvas.height = window.innerHeight;
    createStars();
  }

  function createStars() {
    stars = [];
    for (let i = 0; i < 300; i++) {
      stars.push({
        x: Math.random() * w,
        y: Math.random() * h,
        r: Math.random() * 1.5 + 0.5,
        d: Math.random() * 0.2 + 0.05
      });
    }
  }

  function drawStars() {
    ctx.clearRect(0, 0, w, h);
    ctx.fillStyle = 'white';
    for (let s of stars) {
      ctx.beginPath();
      ctx.arc(s.x, s.y, s.r, 0, Math.PI * 2);
      ctx.fill();
    }
    moveStars();
  }

  function moveStars() {
    for (let s of stars) {
      s.y += s.d;
      if (s.y > h) {
        s.y = 0;
        s.x = Math.random() * w;
      }
    }
  }

  function animate() {
    drawStars();
    requestAnimationFrame(animate);
  }

  window.addEventListener('resize', resizeCanvas);
  resizeCanvas();
  animate();