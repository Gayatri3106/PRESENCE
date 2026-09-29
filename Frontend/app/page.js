import Link from 'next/link';

export default function Home() {
  return <main className="min-h-screen relative flex flex-col overflow-hidden bg-background">
    <video className="absolute inset-0 w-full h-full object-cover z-0" src="https://d8j0ntlcm91z4.cloudfront.net/user_38xzZboKViGWJOttwIXH07lWA1P/hf_20260314_131748_f2ca2a28-fed7-44c8-b9a9-bd9acdd5ec31.mp4" autoPlay loop muted playsInline />
    <nav className="relative z-10 flex items-center justify-between px-8 py-6 max-w-7xl mx-auto w-full">
      <div className="text-3xl tracking-tight" style={{fontFamily:'var(--font-display)'}}>Presence<sup className="text-xs">®</sup></div>
      <div className="hidden md:flex gap-8 text-sm"><Link href="/">Home</Link><Link href="/login" className="text-white/60 hover:text-white">Student</Link><Link href="/admin/login" className="text-white/60 hover:text-white">Faculty</Link></div>
      <Link href="/signup" className="liquid-glass rounded-full px-6 py-2.5 text-sm hover:scale-[1.03] transition-transform">Register Face</Link>
    </nav>
    <section className="relative z-10 flex-1 flex flex-col items-center justify-center text-center px-6 py-24">
      <h1 className="text-6xl sm:text-8xl leading-[.95] tracking-[-2.5px] max-w-6xl animate-fade-rise" style={{fontFamily:'var(--font-display)'}}>Where <em className="not-italic text-white/55">presence</em> meets <em className="not-italic text-white/55">verification.</em></h1>
      <p className="text-white/60 max-w-2xl mt-8 text-base sm:text-lg leading-relaxed animate-fade-rise-delay">Secure classroom attendance using 128-dimensional facial embeddings, Euclidean face verification and rotating QR authentication.</p>
      <div className="flex flex-wrap justify-center gap-4 mt-12 animate-fade-rise-delay-2"><Link href="/login" className="bg-white text-black rounded-full px-10 py-4 hover:scale-[1.03] transition-transform">Student Login</Link><Link href="/admin/login" className="liquid-glass rounded-full px-10 py-4 hover:scale-[1.03] transition-transform">Faculty Portal</Link></div>
    </section>
  </main>;
}
