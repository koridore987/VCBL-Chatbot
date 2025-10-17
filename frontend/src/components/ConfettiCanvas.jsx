import { useEffect, useRef } from 'react'

const DEFAULT_COLORS = ['#34d399', '#60a5fa', '#f472b6', '#facc15', '#a78bfa']

const createParticle = (width, height, colors) => ({
  x: Math.random() * width,
  y: -20,
  velocityX: (Math.random() - 0.5) * 6,
  velocityY: 4 + Math.random() * 3,
  gravity: 0.15 + Math.random() * 0.1,
  rotation: Math.random() * 360,
  rotationSpeed: (Math.random() - 0.5) * 12,
  size: 6 + Math.random() * 8,
  color: colors[Math.floor(Math.random() * colors.length)],
  alpha: 0.9,
})

const ConfettiCanvas = ({ active, duration = 2800, colors = DEFAULT_COLORS, className = '' }) => {
  const canvasRef = useRef(null)

  useEffect(() => {
    if (!active) return undefined

    const canvas = canvasRef.current
    if (!canvas) return undefined

    const ctx = canvas.getContext('2d')
    if (!ctx) return undefined

    const dpr = window.devicePixelRatio || 1
    const resize = () => {
      const { offsetWidth, offsetHeight } = canvas
      canvas.width = offsetWidth * dpr
      canvas.height = offsetHeight * dpr
      ctx.setTransform(dpr, 0, 0, dpr, 0, 0)
      ctx.clearRect(0, 0, offsetWidth, offsetHeight)
    }

    resize()
    const handleResize = () => resize()
    window.addEventListener('resize', handleResize)

    const particles = Array.from({ length: 120 }, () =>
      createParticle(canvas.offsetWidth, canvas.offsetHeight, colors)
    )

    const start = performance.now()
    let animationFrame

    const draw = (time) => {
      const elapsed = time - start
      const width = canvas.offsetWidth
      const height = canvas.offsetHeight

      ctx.clearRect(0, 0, width, height)

      particles.forEach((particle, index) => {
        particle.x += particle.velocityX
        particle.y += particle.velocityY
        particle.velocityY += particle.gravity
        particle.rotation += particle.rotationSpeed
        particle.alpha -= 0.003

        if (particle.y > height + 30 || particle.alpha <= 0) {
          particles[index] = createParticle(width, height, colors)
          particles[index].y = -20
        }

        ctx.save()
        ctx.globalAlpha = Math.max(particle.alpha, 0)
        ctx.translate(particle.x, particle.y)
        ctx.rotate((particle.rotation * Math.PI) / 180)
        ctx.fillStyle = particle.color
        ctx.fillRect(-particle.size / 2, -particle.size / 2, particle.size, particle.size * 0.6)
        ctx.restore()
      })

      if (elapsed < duration) {
        animationFrame = requestAnimationFrame(draw)
      } else {
        ctx.clearRect(0, 0, width, height)
      }
    }

    animationFrame = requestAnimationFrame(draw)

    return () => {
      cancelAnimationFrame(animationFrame)
      window.removeEventListener('resize', handleResize)
      ctx.clearRect(0, 0, canvas.offsetWidth, canvas.offsetHeight)
    }
  }, [active, duration, colors])

  return <canvas ref={canvasRef} className={className} />
}

export default ConfettiCanvas
