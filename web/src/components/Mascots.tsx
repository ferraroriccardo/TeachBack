// Original hand-drawn SVG mascots: the chick is the Sub-student, the owl is the Teacher.
export function Chick({ size = 40 }: { size?: number }) {
  return (
    <svg width={size} height={size} viewBox="0 0 40 40" aria-hidden="true">
      <circle cx="20" cy="20" r="20" fill="#FFF3C4" />
      <path d="M20 8c1.5-3 4-3 4-3s-1 2.2-2.4 3.4" fill="none" stroke="#E39B2D" strokeWidth="1.6" strokeLinecap="round" />
      <ellipse cx="20" cy="22" rx="11" ry="11.5" fill="#FFCF3F" />
      <circle cx="16" cy="20" r="1.8" fill="#18213D" />
      <circle cx="24" cy="20" r="1.8" fill="#18213D" />
      <circle cx="16.6" cy="19.4" r=".6" fill="#fff" />
      <circle cx="24.6" cy="19.4" r=".6" fill="#fff" />
      <path d="M18 24h4l-2 2.6z" fill="#E39B2D" />
      <circle cx="13.4" cy="24.4" r="1.6" fill="#FFB199" opacity=".7" />
      <circle cx="26.6" cy="24.4" r="1.6" fill="#FFB199" opacity=".7" />
    </svg>
  )
}

export function Owl({ size = 40 }: { size?: number }) {
  return (
    <svg width={size} height={size} viewBox="0 0 40 40" aria-hidden="true">
      <circle cx="20" cy="20" r="20" fill="#ECE7FF" />
      <path d="M10 13l4 3M30 13l-4 3" stroke="#4B33B5" strokeWidth="2" strokeLinecap="round" />
      <ellipse cx="20" cy="23" rx="11" ry="11" fill="#6A4BE0" />
      <ellipse cx="20" cy="27" rx="6.5" ry="6" fill="#B9A9FF" />
      <circle cx="15.5" cy="20" r="4" fill="#fff" />
      <circle cx="24.5" cy="20" r="4" fill="#fff" />
      <circle cx="15.5" cy="20" r="1.8" fill="#18213D" />
      <circle cx="24.5" cy="20" r="1.8" fill="#18213D" />
      <path d="M18.6 23.4h2.8L20 25.6z" fill="#FFCF3F" />
    </svg>
  )
}
