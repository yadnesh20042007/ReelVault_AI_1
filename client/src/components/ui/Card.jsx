export function Card({ children, className = '', ...props }) {
  return (
    <div className={`bg-white rounded-2xl border border-[#E3D4F8] shadow-[0_4px_20px_-4px_rgba(139,92,246,0.05)] ${className}`} {...props}>
      {children}
    </div>
  );
}

export function CardHeader({ children, className = '' }) {
  return <div className={`px-6 py-4 border-b border-[#E3D4F8]/60 ${className}`}>{children}</div>;
}

export function CardContent({ children, className = '' }) {
  return <div className={`p-6 ${className}`}>{children}</div>;
}

export function CardFooter({ children, className = '' }) {
  return <div className={`px-6 py-4 border-t border-[#E3D4F8]/60 bg-[#FBF7FD] rounded-b-2xl ${className}`}>{children}</div>;
}
