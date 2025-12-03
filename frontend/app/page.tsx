import { redirect } from "next/navigation";
import { cookies } from "next/headers";

export const dynamic = "force-dynamic";
export const revalidate = 0;

export default async function Home() {
  // Always perform authentication check at request time
  const cookieStore = await cookies();
  const token = cookieStore.get("session_token")?.value;

  console.log("[ROOT PAGE] Executing with token:", token ? "present" : "missing");

  if (token) {
    console.log("[ROOT PAGE] Redirecting to /dashboard");
    redirect("/dashboard");
  } else {
    console.log("[ROOT PAGE] Redirecting to /login");
    redirect("/login");
  }
}
