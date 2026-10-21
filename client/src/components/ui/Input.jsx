export default function Input({ className = '', ...props }) {
  return (
    <input
      className={`w-full px-4 py-2.5 bg-white border border-[#E3D4F8] rounded-xl text-[#261B33] placeholder:text-[#776A83]/50 focus:outline-none focus:border-[#8B5CF6] focus:ring-2 focus:ring-[#8B5CF6]/20 transition-all ${className}`}
      {...props}
    />
  );
}
