import { redirect } from "next/navigation";
import { cookies } from "next/headers";

const SESSION_COOKIE =
  process.env.JWT_COOKIE_NAME ?? "deal_room_ai_session";

export default async function Home() {
  const jar = await cookies();
  const hasSession = Boolean(jar.get(SESSION_COOKIE)?.value);
  redirect(hasSession ? "/deal-rooms" : "/login");
}
