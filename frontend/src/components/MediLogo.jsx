export default function MediLogo({ size = 40 }) {
  return (
    <svg
      width={size}
      height={size}
      viewBox="0 0 100 100"
      fill="none"
      xmlns="http://www.w3.org/2000/svg"
    >
      {/* Background rounded square */}
      <rect width="100" height="100" rx="22" fill="url(#bgGrad)" />

      {/* Plus / Cross */}
      <rect x="38" y="18" width="24" height="64" rx="6" fill="white" />
      <rect x="18" y="38" width="64" height="24" rx="6" fill="white" />

      {/* Glowing dot - top left of cross */}
      <circle cx="36" cy="34" r="6" fill="#7dd3fc" opacity="0.9" />
      <circle cx="36" cy="34" r="3" fill="white" opacity="0.95" />

      {/* Glowing dot - bottom right of cross */}
      <circle cx="64" cy="66" r="6" fill="#7dd3fc" opacity="0.9" />
      <circle cx="64" cy="66" r="3" fill="white" opacity="0.95" />

      <defs>
        <linearGradient id="bgGrad" x1="0" y1="0" x2="100" y2="100" gradientUnits="userSpaceOnUse">
          <stop offset="0%" stopColor="#1e4db7" />
          <stop offset="100%" stopColor="#1340a0" />
        </linearGradient>
      </defs>
    </svg>
  )
}
