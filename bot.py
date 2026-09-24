<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0, user-scalable=no">
  <title>Cosmic Flipper – Space Pinball</title>
  <style>
    * { margin: 0; padding: 0; box-sizing: border-box; }
    body {
      background: #050510;
      color: white;
      font-family: 'Segoe UI', system-ui, sans-serif;
      display: flex;
      flex-direction: column;
      align-items: center;
      justify-content: center;
      min-height: 100vh;
      overflow: hidden;
      touch-action: none;
    }
    h1 {
      font-size: 1.8rem;
      margin-bottom: 8px;
      background: linear-gradient(90deg, #7af, #f7a, #7af);
      -webkit-background-clip: text;
      -webkit-text-fill-color: transparent;
      text-shadow: 0 0 20px rgba(100,180,255,0.4);
    }
    #ui {
      display: flex;
      gap: 30px;
      margin-bottom: 12px;
      font-size: 1.2rem;
      font-weight: 600;
    }
    #game-container {
      position: relative;
      border: 3px solid #3a5a9a;
      border-radius: 12px;
      box-shadow: 0 0 40px rgba(80,140,255,0.3), inset 0 0 60px rgba(0,30,80,0.6);
      background: #020208;
    }
    canvas {
      display: block;
      border-radius: 9px;
    }
    #message {
      position: absolute;
      top: 50%;
      left: 50%;
      transform: translate(-50%, -50%);
      font-size: 1.8rem;
      font-weight: bold;
      text-align: center;
      text-shadow: 0 0 15px #0ff;
      pointer-events: none;
      opacity: 0;
      transition: opacity 0.3s;
    }
    #message.show { opacity: 1; }
    .controls {
      margin-top: 16px;
      text-align: center;
      color: #8af;
      font-size: 0.95rem;
    }
    .btn {
      margin-top: 14px;
      padding: 10px 28px;
      font-size: 1.1rem;
      background: linear-gradient(90deg, #2060c0, #40a0ff);
      border: none;
      border-radius: 30px;
      color: white;
      cursor: pointer;
      box-shadow: 0 0 20px rgba(60,140,255,0.5);
      transition: transform 0.15s;
    }
    .btn:active { transform: scale(0.96); }
  </style>
</head>
<body>
  <h1>🌌 COSMIC FLIPPER</h1>
  <div id="ui">
    <div>Score: <span id="score">0</span></div>
    <div>Lives: <span id="lives">3</span></div>
  </div>

  <div id="game-container">
    <canvas id="canvas" width="400" height="600"></canvas>
    <div id="message"></div>
  </div>

  <div class="controls">
    ← → or A D or tap sides to flip<br>
    Space / Tap center to launch
  </div>
  <button class="btn" id="restartBtn" style="display:none">Play Again</button>

  <script>
    const canvas = document.getElementById('canvas');
    const ctx = canvas.getContext('2d');
    const scoreEl = document.getElementById('score');
    const livesEl = document.getElementById('lives');
    const messageEl = document.getElementById('message');
    const restartBtn = document.getElementById('restartBtn');

    // Game state
    let score = 0;
    let lives = 3;
    let gameOver = false;
    let ballLaunched = false;

    // Ball
    const ball = {
      x: 200,
      y: 520,
      vx: 0,
      vy: 0,
      radius: 9,
      speed: 0
    };

    // Flippers
    const leftFlipper = {
      x: 110,
      y: 520,
      angle: 0.4,
      targetAngle: 0.4,
      length: 70,
      active: false
    };
    const rightFlipper = {
      x: 290,
      y: 520,
      angle: -0.4,
      targetAngle: -0.4,
      length: 70,
      active: false
    };

    // Bumpers (planets)
    const bumpers = [
      { x: 120, y: 180, r: 28, color: '#e8a838', points: 50, name: 'Jupiter' },
      { x: 280, y: 160, r: 22, color: '#c0c0c0', points: 40, name: 'Moon' },
      { x: 200, y: 280, r: 32, color: '#222', points: 100, name: 'Black Hole' },
      { x: 90,  y: 340, r: 20, color: '#4a9eff', points: 30, name: 'Earth' },
      { x: 310, y: 320, r: 18, color: '#ff5533', points: 30, name: 'Mars' },
      { x: 200, y: 120, r: 16, color: '#ffcc00', points: 60, name: 'Sun' }
    ];

    // Stars background
    const stars = Array.from({length: 120}, () => ({
      x: Math.random() * 400,
      y: Math.random() * 600,
      s: Math.random() * 1.8 + 0.3
    }));

    // Physics
    const gravity = 0.18;
    const friction = 0.995;
    const bounce = 0.75;

    function resetBall() {
      ball.x = 200;
      ball.y = 520;
      ball.vx = 0;
      ball.vy = 0;
      ballLaunched = false;
    }

    function launchBall() {
      if (ballLaunched || gameOver) return;
      ballLaunched = true;
      ball.vx = (Math.random() - 0.5) * 3;
      ball.vy = -14 - Math.random() * 3;
    }

    function showMessage(text, duration = 1500) {
      messageEl.textContent = text;
      messageEl.classList.add('show');
      setTimeout(() => messageEl.classList.remove('show'), duration);
    }

    function loseLife() {
      lives--;
      livesEl.textContent = lives;
      if (lives <= 0) {
        gameOver = true;
        restartBtn.style.display = 'block';
        showMessage('💥 ASTEROID LOST\nScore: ' + score, 99999);
      } else {
        showMessage('Life lost!');
        resetBall();
      }
    }

    // Collision helpers
    function circleRectCollision() { /* not needed */ }

    function checkBumperCollision(b) {
      const dx = ball.x - b.x;
      const dy = ball.y - b.y;
      const dist = Math.sqrt(dx*dx + dy*dy);
      if (dist < ball.radius + b.r) {
        // Push out
        const overlap = ball.radius + b.r - dist;
        const nx = dx / dist;
        const ny = dy / dist;
        ball.x += nx * overlap;
        ball.y += ny * overlap;

        // Reflect velocity
        const dot = ball.vx * nx + ball.vy * ny;
        ball.vx -= 2 * dot * nx;
        ball.vy -= 2 * dot * ny;

        // Boost a bit
        ball.vx *= 1.1;
        ball.vy *= 1.1;

        score += b.points;
        scoreEl.textContent = score;
        return true;
      }
      return false;
    }

    function checkFlipper(f, isLeft) {
      // Simple line-circle collision for flipper
      const cos = Math.cos(f.angle);
      const sin = Math.sin(f.angle);
      const endX = f.x + cos * f.length * (isLeft ? 1 : -1);
      const endY = f.y + sin * f.length;

      // Closest point on flipper segment
      let t = ((ball.x - f.x) * (endX - f.x) + (ball.y - f.y) * (endY - f.y)) / (f.length * f.length);
      t = Math.max(0, Math.min(1, t));
      const closestX = f.x + t * (endX - f.x);
      const closestY = f.y + t * (endY - f.y);

      const dx = ball.x - closestX;
      const dy = ball.y - closestY;
      const dist = Math.sqrt(dx*dx + dy*dy);

      if (dist < ball.radius + 6) {
        const nx = dx / (dist || 1);
        const ny = dy / (dist || 1);
        ball.x = closestX + nx * (ball.radius + 6);
        ball.y = closestY + ny * (ball.radius + 6);

        // Bounce
        const dot = ball.vx * nx + ball.vy * ny;
        ball.vx -= 1.8 * dot * nx;
        ball.vy -= 1.8 * dot * ny;

        // Extra power if flipper is moving up
        if (f.active) {
          ball.vy -= 6;
          ball.vx += isLeft ? -2 : 2;
        }
        return true;
      }
      return false;
    }

    function update() {
      if (gameOver) return;

      // Flipper animation
      leftFlipper.angle += (leftFlipper.targetAngle - leftFlipper.angle) * 0.35;
      rightFlipper.angle += (rightFlipper.targetAngle - rightFlipper.angle) * 0.35;

      if (!ballLaunched) return;

      // Physics
      ball.vy += gravity;
      ball.vx *= friction;
      ball.vy *= friction;
      ball.x += ball.vx;
      ball.y += ball.vy;

      // Walls
      if (ball.x < ball.radius + 8) {
        ball.x = ball.radius + 8;
        ball.vx *= -bounce;
      }
      if (ball.x > 400 - ball.radius - 8) {
        ball.x = 400 - ball.radius - 8;
        ball.vx *= -bounce;
      }
      if (ball.y < ball.radius + 8) {
        ball.y = ball.radius + 8;
        ball.vy *= -bounce;
      }

      // Drain
      if (ball.y > 600 + 20) {
        loseLife();
        return;
      }

      // Bumpers
      for (const b of bumpers) checkBumperCollision(b);

      // Flippers
      checkFlipper(leftFlipper, true);
      checkFlipper(rightFlipper, false);
    }

    function draw() {
      // Background
      ctx.fillStyle = '#020208';
      ctx.fillRect(0, 0, 400, 600);

      // Stars
      ctx.fillStyle = '#ffffff';
      for (const s of stars) {
        ctx.globalAlpha = 0.4 + Math.sin(Date.now()/700 + s.x) * 0.3;
        ctx.beginPath();
        ctx.arc(s.x, s.y, s.s, 0, Math.PI*2);
        ctx.fill();
      }
      ctx.globalAlpha = 1;

      // Side walls glow
      ctx.strokeStyle = '#1a3a6a';
      ctx.lineWidth = 14;
      ctx.beginPath();
      ctx.moveTo(6, 0);
      ctx.lineTo(6, 600);
      ctx.moveTo(394, 0);
      ctx.lineTo(394, 600);
      ctx.stroke();

      // Bumpers
      for (const b of bumpers) {
        // Glow
        const grad = ctx.createRadialGradient(b.x, b.y, 0, b.x, b.y, b.r*1.6);
        grad.addColorStop(0, b.color);
        grad.addColorStop(1, 'transparent');
        ctx.fillStyle = grad;
        ctx.beginPath();
        ctx.arc(b.x, b.y, b.r*1.6, 0, Math.PI*2);
        ctx.fill();

        // Planet
        ctx.beginPath();
        ctx.arc(b.x, b.y, b.r, 0, Math.PI*2);
        ctx.fillStyle = b.color;
        ctx.fill();
        ctx.strokeStyle = 'rgba(255,255,255,0.3)';
        ctx.lineWidth = 2;
        ctx.stroke();
      }

      // Flippers
      function drawFlipper(f, isLeft) {
        ctx.save();
        ctx.translate(f.x, f.y);
        ctx.rotate(f.angle);
        ctx.fillStyle = '#4af';
        ctx.shadowColor = '#0ff';
        ctx.shadowBlur = 15;
        ctx.fillRect(isLeft ? 0 : -f.length, -7, f.length, 14);
        ctx.shadowBlur = 0;
        ctx.restore();
      }
      drawFlipper(leftFlipper, true);
      drawFlipper(rightFlipper, false);

      // Ball (asteroid)
      if (ballLaunched || !gameOver) {
        const grad = ctx.createRadialGradient(ball.x-3, ball.y-3, 0, ball.x, ball.y, ball.radius);
        grad.addColorStop(0, '#fff');
        grad.addColorStop(0.4, '#ffcc66');
        grad.addColorStop(1, '#cc6600');
        ctx.beginPath();
        ctx.arc(ball.x, ball.y, ball.radius, 0, Math.PI*2);
        ctx.fillStyle = grad;
        ctx.fill();
        ctx.strokeStyle = '#ffaa00';
        ctx.lineWidth = 1.5;
        ctx.stroke();
      }

      // Launch indicator
      if (!ballLaunched && !gameOver) {
        ctx.fillStyle = 'rgba(100,200,255,0.7)';
        ctx.font = '16px sans-serif';
        ctx.textAlign = 'center';
        ctx.fillText('PRESS SPACE / TAP TO LAUNCH', 200, 480);
      }
    }

    function loop() {
      update();
      draw();
      requestAnimationFrame(loop);
    }

    // Controls
    function setLeft(active) {
      leftFlipper.active = active;
      leftFlipper.targetAngle = active ? -0.5 : 0.4;
    }
    function setRight(active) {
      rightFlipper.active = active;
      rightFlipper.targetAngle = active ? 0.5 : -0.4;
    }

    document.addEventListener('keydown', e => {
      if (e.code === 'ArrowLeft' || e.code === 'KeyA') setLeft(true);
      if (e.code === 'ArrowRight' || e.code === 'KeyD') setRight(true);
      if (e.code === 'Space') launchBall();
    });
    document.addEventListener('keyup', e => {
      if (e.code === 'ArrowLeft' || e.code === 'KeyA') setLeft(false);
      if (e.code === 'ArrowRight' || e.code === 'KeyD') setRight(false);
    });

    // Touch controls
    canvas.addEventListener('touchstart', e => {
      e.preventDefault();
      const rect = canvas.getBoundingClientRect();
      const x = (e.touches[0].clientX - rect.left) * (400 / rect.width);
      if (!ballLaunched) {
        launchBall();
        return;
      }
      if (x < 200) setLeft(true);
      else setRight(true);
    });
    canvas.addEventListener('touchend', e => {
      e.preventDefault();
      setLeft(false);
      setRight(false);
    });

    // Mouse (for desktop testing)
    canvas.addEventListener('mousedown', e => {
      const rect = canvas.getBoundingClientRect();
      const x = (e.clientX - rect.left) * (400 / rect.width);
      if (!ballLaunched) launchBall();
      else if (x < 200) setLeft(true);
      else setRight(true);
    });
    canvas.addEventListener('mouseup', () => {
      setLeft(false);
      setRight(false);
    });

    restartBtn.addEventListener('click', () => {
      score = 0;
      lives = 3;
      gameOver = false;
      scoreEl.textContent = 0;
      livesEl.textContent = 3;
      restartBtn.style.display = 'none';
      messageEl.classList.remove('show');
      resetBall();
    });

    // Start
    loop();
  </script>
</body>
</html>
