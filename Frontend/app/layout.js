import './globals.css';

export const metadata = {
  title: 'Presence — Secure Attendance',
  description: 'Face-verified classroom attendance with dynamic QR authentication.',
};

export default function RootLayout({ children }) {
  return (
    <html lang="en" className="dark">
      <head>
        <link rel="preconnect" href="https://fonts.googleapis.com" />
        <link rel="preconnect" href="https://fonts.gstatic.com" crossOrigin="anonymous" />
        <link href="https://fonts.googleapis.com/css2?family=Instrument+Serif:ital@0;1&family=Inter:wght@400;500&display=swap" rel="stylesheet" />
      </head>
      <body className="bg-[#121212] text-white min-h-screen font-sans antialiased">
        {children}
      </body>
    </html>
  );
}
