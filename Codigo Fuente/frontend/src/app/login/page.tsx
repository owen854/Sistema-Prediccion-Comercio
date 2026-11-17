import Link from "next/link";

export default function LoginPage() {
  return (
    <main className="bg-ledger-grid flex min-h-screen items-center justify-center p-4">
      <section className="w-full max-w-sm rounded-md border border-[#E2E8F0] bg-white p-6 shadow-sm">
        <h1 className="text-xl font-bold">Iniciar sesión</h1>
        <p className="mt-2 text-sm text-[#475569]">
          La autenticación con roles (administrador, analista y comerciante) se implementa en el
          Sprint 2 (RF-62, RF-63).
        </p>
        <Link href="/" className="mt-4 inline-block text-sm font-semibold text-[#B45309] hover:underline">
          Ir al panel
        </Link>
      </section>
    </main>
  );
}
