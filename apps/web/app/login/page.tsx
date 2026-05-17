import { cookies } from "next/headers";
import { redirect } from "next/navigation";
import {
  getOwnerSessionToken,
  isOwnerAuthRequired,
  OWNER_SESSION_COOKIE,
  ownerAuthConfigError,
  verifyOwnerPassword
} from "../../lib/ownerAuth";

type LoginPageProps = {
  searchParams?: Promise<{ error?: string; next?: string }> | { error?: string; next?: string };
};

export default async function LoginPage({ searchParams }: LoginPageProps) {
  const resolvedSearchParams = await Promise.resolve(searchParams ?? {});
  const configError = ownerAuthConfigError();
  const nextPath = sanitizeNextPath(resolvedSearchParams.next);

  if (!isOwnerAuthRequired()) {
    redirect(nextPath);
  }

  return (
    <main className="loginPage" aria-labelledby="owner-login-title">
      <section className="loginPanel">
        <div>
          <p className="pageEyebrow">管理员访问</p>
          <h1 className="pageTitle" id="owner-login-title">
            SignalForge 本地生产登录
          </h1>
          <p className="pageSubtitle">
            请输入 Mac mini 单人生产环境密码。会话使用 HttpOnly cookie 保存，不在前端代码中保存密钥。
          </p>
        </div>
        {configError ? (
          <section className="stateBlock errorBlock" role="alert">
            <h2 className="stateTitle">认证配置缺失</h2>
            <p className="stateText">{configError}</p>
          </section>
        ) : null}
        {resolvedSearchParams.error === "invalid" ? (
          <p className="inlineError" role="alert">
            密码不正确，未创建管理员会话。
          </p>
        ) : null}
        <form action={loginOwner} className="formGrid">
          <input name="next" type="hidden" value={nextPath} />
          <label className="formField">
            <span>管理员密码</span>
            <input
              autoComplete="current-password"
              disabled={Boolean(configError)}
              name="password"
              required
              type="password"
            />
          </label>
          <button className="button buttonPrimary buttonLarge" disabled={Boolean(configError)} type="submit">
            登录
          </button>
        </form>
      </section>
    </main>
  );
}

async function loginOwner(formData: FormData) {
  "use server";

  const password = String(formData.get("password") ?? "");
  const nextPath = sanitizeNextPath(String(formData.get("next") ?? ""));
  const sessionToken = getOwnerSessionToken();

  if (!sessionToken || !verifyOwnerPassword(password)) {
    redirect(`/login?error=invalid&next=${encodeURIComponent(nextPath)}`);
  }

  const cookieStore = await cookies();
  cookieStore.set({
    name: OWNER_SESSION_COOKIE,
    value: sessionToken,
    httpOnly: true,
    sameSite: "lax",
    secure: process.env.NODE_ENV === "production",
    path: "/",
    maxAge: 60 * 60 * 12
  });

  redirect(nextPath);
}

function sanitizeNextPath(value: string | undefined | null): string {
  if (!value || !value.startsWith("/") || value.startsWith("//")) {
    return "/signals";
  }

  if (value.startsWith("/login")) {
    return "/signals";
  }

  return value;
}
