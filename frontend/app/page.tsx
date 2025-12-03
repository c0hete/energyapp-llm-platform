import { redirect } from "next/navigation";
import { cookies } from "next/headers";

export const dynamic = "force-dynamic";

export default async function Home() {
  const cookieStore = await cookies();
  const token = cookieStore.get("session_token");

  if (token?.value) {
    redirect("/dashboard");
  } else {
    redirect("/login");
  }
}
