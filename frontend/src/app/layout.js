import '../styles/globals.css';
import Header from '../components/Header';
import Footer from '../components/Footer';

export const metadata = {
  title: 'HustleYetu — Civic Literacy & Policy Impact Platform',
  description: 'Proactive alerts, financial impact modeling, and regulatory compliance guidance on Kenyan transport and finance bills.',
};

export default function RootLayout({ children }) {
  return (
    <html lang="en">
      <head>
        <meta name="viewport" content="width=device-width, initial-scale=1.0" />
      </head>
      <body>
        <div className="app-shell">
          {/* Header Navigation */}
          <Header />

          {/* Main Content Area */}
          <main style={{ flex: '1 0 auto', padding: '1.5rem 0 3rem 0' }}>
            <div className="container">
              {children}
            </div>
          </main>

          {/* Global Footer */}
          <Footer />
        </div>
      </body>
    </html>
  );
}
