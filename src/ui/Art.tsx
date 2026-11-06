/** Brand art: logo mark and Whyz, the curious mascot. Decorative, so hidden from screen readers. */

export function LogoMark({ size = 34 }: { size?: number }) {
  return (
    <svg width={size} height={size} viewBox="0 0 34 34" aria-hidden="true">
      <rect x="2" y="2" width="30" height="30" rx="9" fill="var(--blue)" />
      <path d="M12.5 13.2c0-2.6 2-4.4 4.6-4.4 2.6 0 4.5 1.7 4.5 4 0 3.4-4.2 3.6-4.2 6.6" fill="none" stroke="#fff" strokeWidth="2.8" strokeLinecap="round" />
      <circle cx="17.4" cy="24.6" r="2" fill="var(--orange)" />
    </svg>
  );
}

export function Whyz({ className = 'wz-mascot', mood = 'happy' }: { className?: string; mood?: 'happy' | 'proud' }) {
  return (
    <svg className={className} width="52" height="60" viewBox="0 0 52 60" aria-hidden="true">
      <path d="M26 2c5 0 8 3 8 7 0 3-2 5-5 6" fill="none" stroke="var(--orange)" strokeWidth="3" strokeLinecap="round" />
      <circle cx="28.5" cy="15.5" r="2.5" fill="var(--orange)" />
      <ellipse cx="26" cy="38" rx="22" ry="20" fill="var(--blue)" />
      <circle cx="18" cy="35" r="5.5" fill="#fff" />
      <circle cx="34" cy="35" r="5.5" fill="#fff" />
      <circle cx="19.5" cy="35.5" r="2.6" fill="var(--ink)" />
      <circle cx="35.5" cy="35.5" r="2.6" fill="var(--ink)" />
      {mood === 'proud' ? (
        <path d="M18 45c4 5 12 5 16 0" fill="#fff" stroke="#fff" strokeWidth="2" strokeLinejoin="round" />
      ) : (
        <path d="M20 46c3.5 3 8.5 3 12 0" fill="none" stroke="#fff" strokeWidth="2.5" strokeLinecap="round" />
      )}
    </svg>
  );
}

export function Check({ ok, size = 18 }: { ok: boolean; size?: number }) {
  return ok ? (
    <svg width={size} height={size} viewBox="0 0 18 18" aria-hidden="true" className="wz-icon-ok">
      <circle cx="9" cy="9" r="8" fill="none" stroke="currentColor" strokeWidth="2" />
      <path d="M5 9.2l2.6 2.6L13 6.4" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" />
    </svg>
  ) : (
    <svg width={size} height={size} viewBox="0 0 18 18" aria-hidden="true" className="wz-icon-no">
      <circle cx="9" cy="9" r="8" fill="none" stroke="currentColor" strokeWidth="2" />
      <path d="M6 6l6 6M12 6l-6 6" stroke="currentColor" strokeWidth="2" strokeLinecap="round" />
    </svg>
  );
}

export function RecipeIcon() {
  return (
    <svg width="22" height="22" viewBox="0 0 22 22" aria-hidden="true">
      <rect x="3" y="2" width="16" height="18" rx="3" fill="none" stroke="currentColor" strokeWidth="2" />
      <path d="M7 7h8M7 11h8M7 15h5" stroke="currentColor" strokeWidth="2" strokeLinecap="round" />
    </svg>
  );
}
