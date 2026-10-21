export default function Button({ 
  children, 
  variant = 'primary', 
  size = 'md', 
  className = '', 
  ...props 
}) {
  const baseStyles = 'inline-flex items-center justify-center font-medium rounded-xl transition-all cursor-pointer focus:outline-none focus:ring-2 focus:ring-offset-2';
  
  const variants = {
    primary: 'bg-gradient-to-r from-[#8B5CF6] to-[#6D28D9] text-white hover:from-[#7C3AED] hover:to-[#5B21B6] focus:ring-[#8B5CF6] shadow-sm shadow-[#8B5CF6]/20 font-bold',
    secondary: 'bg-[#F0E8FF] text-[#6D28D9] hover:bg-[#E3D4F8] focus:ring-[#8B5CF6] font-semibold',
    outline: 'border border-[#E3D4F8] bg-white text-[#261B33] hover:bg-[#FBF7FD] hover:border-[#8B5CF6] focus:ring-[#8B5CF6] font-semibold',
    ghost: 'bg-transparent text-[#776A83] hover:bg-[#F0E8FF] hover:text-[#261B33] focus:ring-[#8B5CF6]'
  };

  const sizes = {
    sm: 'text-sm px-3 py-1.5',
    md: 'text-sm px-4 py-2',
    lg: 'text-base px-6 py-3',
    icon: 'p-2'
  };

  return (
    <button 
      className={`${baseStyles} ${variants[variant]} ${sizes[size]} ${className}`}
      {...props}
    >
      {children}
    </button>
  );
}
