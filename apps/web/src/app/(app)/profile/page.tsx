import { SectionHeader } from "@/components/ui/section-header";
import { ProfileForm } from "@/features/profile/profile-form";


export default function ProfilePage() {
  return (
    <div className="space-y-8">
      <SectionHeader
        eyebrow="Profile"
        title="个人资料页"
        description="这一页已经接到真实 API，可作为注册后第一个必须完成的资料环节。"
      />
      <ProfileForm />
    </div>
  );
}
