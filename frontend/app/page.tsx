// Root page - handled by middleware.ts
// The middleware will redirect this route based on authentication status
// This empty component ensures the route exists for the middleware to intercept

export const dynamic = "force-dynamic";

export default async function Home() {
  // This component should never render
  // The middleware.ts will redirect before this executes
  return null;
}
