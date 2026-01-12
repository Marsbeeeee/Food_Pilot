window.addEventListener('load', () => {
  playOpeningFireworks();
});

function playOpeningFireworks() {
  const container = document.body;
  const fireworkCount = 6;

  for (let i = 0; i < fireworkCount; i++) {
    setTimeout(() => {
      createFirework(container);
    }, i * 300);
  }
}

function createFirework(container) {
  const firework = document.createElement('div');
  firework.classList.add('mario-firework');

  const x = Math.random() * 80 + 10;
  const y = Math.random() * 60 + 10;

  firework.style.left = `${x}vw`;
  firework.style.top = `${y}vh`;

  // 随机颜色主题 (金、银、铜、红、蓝)
  const colors = ['var(--gold)', 'var(--silver)', 'var(--bronze)', '#ff4d4d', '#4d94ff'];
  const randomColor = colors[Math.floor(Math.random() * colors.length)];
  firework.style.setProperty('--fw-color', randomColor);

  container.appendChild(firework);

  // 动画结束后移除元素，避免污染 DOM
  firework.addEventListener('animationend', () => {
    firework.remove();
  });
}