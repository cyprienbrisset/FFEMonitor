import type { Metadata, Viewport } from 'next'
import { DM_Serif_Display, DM_Sans } from 'next/font/google'
import Script from 'next/script'
import { ServiceWorkerRegistration } from '@/components/ServiceWorkerRegistration'
import { Providers } from '@/components/Providers'
import './globals.css'

const dmSerifDisplay = DM_Serif_Display({
  subsets: ['latin'],
  weight: '400',
  variable: '--font-display',
  display: 'swap',
})

const dmSans = DM_Sans({
  subsets: ['latin'],
  variable: '--font-body',
  display: 'swap',
})

export const metadata: Metadata = {
  title: 'Hoofs',
  description: 'Surveillance des concours FFE - Recevez des notifications dès l\'ouverture des engagements',
  manifest: '/manifest.json',
  icons: {
    icon: [
      { url: '/logo_hoofs.svg', type: 'image/svg+xml' },
      { url: '/icons/icon-192.png', sizes: '192x192', type: 'image/png' },
      { url: '/icons/icon-512.png', sizes: '512x512', type: 'image/png' },
    ],
    apple: [
      { url: '/icons/icon-152.png', sizes: '152x152' },
      { url: '/icons/icon-192.png', sizes: '192x192' },
    ],
  },
  appleWebApp: {
    capable: true,
    statusBarStyle: 'default',
    title: 'Hoofs',
  },
  formatDetection: {
    telephone: false,
  },
  openGraph: {
    title: 'Hoofs',
    description: 'Surveillance des concours FFE - Recevez des notifications dès l\'ouverture des engagements',
    url: 'https://hoofs.fr',
    siteName: 'Hoofs',
    locale: 'fr_FR',
    type: 'website',
  },
}

export const viewport: Viewport = {
  themeColor: '#FAF7F2',
  width: 'device-width',
  initialScale: 1,
  maximumScale: 1,
  userScalable: false,
  viewportFit: 'cover',
}

export default function RootLayout({
  children,
}: {
  children: React.ReactNode
}) {
  const oneSignalAppId = process.env.NEXT_PUBLIC_ONESIGNAL_APP_ID

  return (
    <html lang="fr" className={`${dmSerifDisplay.variable} ${dmSans.variable}`}>
      <head>
        {/* Nettoyer les anciens SW (sw.js) qui pourraient conflictuer AVANT OneSignal */}
        <Script id="sw-cleanup" strategy="beforeInteractive">
          {`
            (async function() {
              if ('serviceWorker' in navigator) {
                var regs = await navigator.serviceWorker.getRegistrations();
                for (var i = 0; i < regs.length; i++) {
                  var sw = regs[i].active || regs[i].installing || regs[i].waiting;
                  if (sw && sw.scriptURL && sw.scriptURL.indexOf('/sw.js') !== -1) {
                    console.log('[SW-Cleanup] Suppression ancien sw.js');
                    await regs[i].unregister();
                  }
                }
              }
            })();
          `}
        </Script>
        <Script
          src="https://cdn.onesignal.com/sdks/web/v16/OneSignalSDK.page.js"
          strategy="afterInteractive"
        />
        {oneSignalAppId && (
          <Script id="onesignal-init" strategy="afterInteractive">
            {`
              window.OneSignalDeferred = window.OneSignalDeferred || [];
              OneSignalDeferred.push(async function(OneSignal) {
                await OneSignal.init({
                  appId: "${oneSignalAppId}",
                  serviceWorkerParam: { scope: "/" },
                  serviceWorkerPath: "/OneSignalSDKWorker.js",
                  allowLocalhostAsSecureOrigin: true,
                  notifyButton: {
                    enable: false,
                  },
                  promptOptions: {
                    slidedown: {
                      prompts: [
                        {
                          type: "push",
                          autoPrompt: true,
                          text: {
                            actionMessage: "Recevoir les notifications d'ouverture des concours ?",
                            acceptButton: "Autoriser",
                            cancelButton: "Plus tard",
                          },
                          delay: {
                            pageViews: 1,
                            timeDelay: 3,
                          },
                        }
                      ]
                    }
                  }
                });
              });
            `}
          </Script>
        )}
      </head>
      <body>
        <Providers>
          <ServiceWorkerRegistration />
          {children}
        </Providers>
      </body>
    </html>
  )
}
