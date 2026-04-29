import { SignalInbox } from "../../components/signals/SignalInbox";

type SignalsPageProps = {
  searchParams: Promise<{
    projectId?: string | string[];
  }>;
};

export default async function SignalsPage({ searchParams }: SignalsPageProps) {
  const params = await searchParams;
  const projectId = Array.isArray(params.projectId) ? params.projectId[0] : params.projectId;

  return <SignalInbox projectId={projectId ?? null} />;
}
