/**
 * Skeleton loading placeholder.
 *
 * Usage:
 *   <Skeleton width="100%" height="20px" />
 *   <Skeleton variant="circle" width="48px" height="48px" />
 *   <Skeleton variant="card" />
 */
export default function Skeleton({ width = '100%', height = '16px', variant = 'text', style = {} }) {
  const baseStyle = {
    background: 'linear-gradient(90deg, #e2e8f0 25%, #f1f5f9 50%, #e2e8f0 75%)',
    backgroundSize: '200% 100%',
    animation: 'shimmer 1.5s ease-in-out infinite',
    borderRadius: variant === 'circle' ? '50%' : '8px',
  }

  const variants = {
    text: { width, height },
    circle: { width, height },
    card: { width: '100%', height: '120px', borderRadius: '16px' },
    button: { width: '120px', height: '40px', borderRadius: '10px' },
  }

  return (
    <>
      <div style={{ ...baseStyle, ...variants[variant], ...style }} />
      <style>{`@keyframes shimmer { 0% { background-position: 200% 0; } 100% { background-position: -200% 0; } }`}</style>
    </>
  )
}

export function SkeletonList({ count = 3, height = '16px', gap = '12px' }) {
  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap }}>
      {Array.from({ length: count }, (_, i) => (
        <Skeleton key={i} height={height} width={i === count - 1 ? '60%' : '100%'} />
      ))}
    </div>
  )
}
