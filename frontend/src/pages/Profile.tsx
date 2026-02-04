
import React, { useState, useEffect } from 'react';
import { UserProfile } from '../main';

interface ProfileProps {
  profile: UserProfile;
  setProfile: React.Dispatch<React.SetStateAction<UserProfile>>;
}

export const Profile: React.FC<ProfileProps> = ({ profile, setProfile }) => {
  const [saveStatus, setSaveStatus] = useState<'idle' | 'saving' | 'success' | 'error'>('idle');

  const handleSave = async () => {
    if (saveStatus === 'saving') return;
    setSaveStatus('saving');
    try {
      await new Promise((resolve) => setTimeout(resolve, 1500));
      setSaveStatus('success');
    } catch (error) {
      setSaveStatus('error');
    }
  };

  useEffect(() => {
    if (saveStatus === 'success' || saveStatus === 'error') {
      const timer = setTimeout(() => {
        setSaveStatus('idle');
      }, 3000);
      return () => clearTimeout(timer);
    }
  }, [saveStatus]);

  const updateProfile = (key: keyof UserProfile, value: any) => {
    setProfile(prev => ({ ...prev, [key]: value }));
  };

  const toggleAllergy = (allergy: string) => {
    setProfile(prev => {
      const exists = prev.allergies.includes(allergy);
      if (exists) {
        return { ...prev, allergies: prev.allergies.filter(a => a !== allergy) };
      }
      return { ...prev, allergies: [...prev.allergies, allergy] };
    });
  };

  return (
    <div className="flex-1 flex flex-col px-8 py-10 max-w-[1200px] mx-auto w-full overflow-y-auto custom-scrollbar relative">
      {saveStatus !== 'idle' && saveStatus !== 'saving' && (
        <div className={`fixed bottom-8 left-1/2 -translate-x-1/2 z-[100] px-6 py-3 rounded-full shadow-2xl flex items-center gap-3 animate-in slide-in-from-bottom-4 duration-300 ${
          saveStatus === 'success' ? 'bg-[#81C784] text-white' : 'bg-red-400 text-white'
        }`}>
          <span className="material-symbols-outlined text-sm font-bold">
            {saveStatus === 'success' ? 'check_circle' : 'error'}
          </span>
          <span className="text-sm font-bold tracking-wide">
            {saveStatus === 'success' ? '更改已成功保存！' : '保存失败，请稍后重试。'}
          </span>
        </div>
      )}

      <div className="flex flex-col md:flex-row justify-between items-start md:items-center mb-12 gap-6">
        <div className="flex flex-col gap-2">
          <h1 className="text-4xl font-serif-brand font-bold text-[#4A453E]">个人档案</h1>
          <p className="text-[#4A453E]/60 text-base max-w-2xl">
            帮助 Food Pilot 了解你的身体状况和生活方式。这些细节能让我们为你提供更个性化、更精准的营养建议。
          </p>
        </div>
        <div className="flex gap-3">
          <button className="px-6 py-3 bg-white text-[#4A453E]/40 font-bold text-sm rounded-full border border-[#4A453E]/10 hover:bg-[#F7F3E9] transition-all">取消</button>
          <button 
            onClick={handleSave}
            disabled={saveStatus === 'saving'}
            className={`flex items-center gap-2 px-8 py-3 font-bold text-sm rounded-full shadow-lg transition-all min-w-[160px] justify-center ${
              saveStatus === 'saving' ? 'bg-[#4A453E]/10 text-[#4A453E]/40 cursor-wait shadow-none' : 'bg-[#FF8A65] text-white shadow-[#FF8A65]/20 hover:translate-y-[-1px]'
            }`}
          >
            {saveStatus === 'saving' ? (
              <><span className="material-symbols-outlined text-sm font-bold animate-spin">progress_activity</span><span>保存中...</span></>
            ) : (
              <><span className="material-symbols-outlined text-sm font-bold">check</span><span>保存更改</span></>
            )}
          </button>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-8 mb-12">
        <div className="space-y-8">
          <div className="bg-white border border-[#4A453E]/05 rounded-[32px] p-8 shadow-sm">
            <div className="flex items-center gap-3 mb-8">
              <div className="size-10 rounded-2xl bg-[#FF8A65]/10 flex items-center justify-center"><span className="material-symbols-outlined text-[#FF8A65]">person</span></div>
              <h3 className="font-serif-brand font-bold text-xl text-[#4A453E]">身体数据</h3>
            </div>
            <div className="grid grid-cols-1 sm:grid-cols-3 gap-6 mb-8">
              <div className="flex flex-col gap-2">
                <label className="text-[10px] font-bold text-[#4A453E]/40 uppercase tracking-widest px-1">年龄</label>
                <input type="number" value={profile.age} onChange={(e) => updateProfile('age', e.target.value)} placeholder="岁" className="w-full bg-[#F7F3E9]/30 border border-[#4A453E]/05 rounded-[18px] px-4 py-3 font-bold text-[#4A453E] focus:ring-2 focus:ring-[#FF8A65]/20 focus:bg-white outline-none transition-all placeholder:text-[#4A453E]/20" />
              </div>
              <div className="flex flex-col gap-2">
                <label className="text-[10px] font-bold text-[#4A453E]/40 uppercase tracking-widest px-1">身高 (cm)</label>
                <input type="number" value={profile.height} onChange={(e) => updateProfile('height', e.target.value)} placeholder="厘米" className="w-full bg-[#F7F3E9]/30 border border-[#4A453E]/05 rounded-[18px] px-4 py-3 font-bold text-[#4A453E] focus:ring-2 focus:ring-[#FF8A65]/20 focus:bg-white outline-none transition-all placeholder:text-[#4A453E]/20" />
              </div>
              <div className="flex flex-col gap-2">
                <label className="text-[10px] font-bold text-[#4A453E]/40 uppercase tracking-widest px-1">体重 (kg)</label>
                <input type="number" value={profile.weight} onChange={(e) => updateProfile('weight', e.target.value)} placeholder="公斤" className="w-full bg-[#F7F3E9]/30 border border-[#4A453E]/05 rounded-[18px] px-4 py-3 font-bold text-[#4A453E] focus:ring-2 focus:ring-[#FF8A65]/20 focus:bg-white outline-none transition-all placeholder:text-[#4A453E]/20" />
              </div>
            </div>
            <div className="flex flex-col gap-2">
              <label className="text-[10px] font-bold text-[#4A453E]/40 uppercase tracking-widest px-1 mb-2">生理性别 (可选)</label>
              <div className="flex flex-wrap gap-2">
                {['男', '女', '不愿透露'].map((sex) => (
                  <label key={sex} className="flex-1 min-w-[120px] group relative flex items-center justify-center p-3 bg-[#F7F3E9]/30 border border-transparent rounded-[18px] cursor-pointer transition-all hover:bg-white hover:border-[#FF8A65]/10 has-[:checked]:border-[#FF8A65] has-[:checked]:bg-white">
                    <input type="radio" name="sex" className="sr-only" checked={profile.sex === sex} onChange={() => updateProfile('sex', sex)} />
                    <span className="text-xs font-bold text-[#4A453E]/60 group-has-[:checked]:text-[#FF8A65]">{sex}</span>
                  </label>
                ))}
              </div>
            </div>
          </div>

          <div className="bg-white border border-[#4A453E]/05 rounded-[32px] p-8 shadow-sm">
            <div className="flex items-center gap-3 mb-8">
              <div className="size-10 rounded-2xl bg-[#81C784]/10 flex items-center justify-center"><span className="material-symbols-outlined text-[#81C784]">directions_run</span></div>
              <h3 className="font-serif-brand font-bold text-xl text-[#4A453E]">生活方式与运动</h3>
            </div>
            <div className="space-y-6">
              <div>
                <label className="block text-[10px] font-bold text-[#4A453E]/40 uppercase tracking-widest px-1 mb-4">日常活动水平</label>
                <div className="grid grid-cols-1 sm:grid-cols-2 gap-2">
                  {[
                    { val: '久坐', desc: '极少或没有运动' },
                    { val: '轻度活动', desc: '每周运动 1-3 天' },
                    { val: '中度活动', desc: '每周运动 3-5 天' },
                    { val: '高度活动', desc: '每周运动 6-7 天' }
                  ].map((act) => (
                    <label key={act.val} className="group flex flex-col p-4 bg-[#F7F3E9]/30 border border-transparent rounded-[24px] cursor-pointer transition-all hover:bg-white hover:border-[#81C784]/20 has-[:checked]:border-[#81C784] has-[:checked]:bg-white overflow-hidden">
                      <input type="radio" name="activity" className="sr-only" checked={profile.activityLevel === act.val} onChange={() => updateProfile('activityLevel', act.val)} />
                      <span className="text-sm font-bold text-[#4A453E] group-has-[:checked]:text-[#81C784] truncate">{act.val}</span>
                      <span className="text-[10px] text-[#4A453E]/40 font-bold uppercase mt-1 truncate">{act.desc}</span>
                    </label>
                  ))}
                </div>
              </div>
            </div>
          </div>
        </div>

        <div className="space-y-8">
          <div className="bg-white border border-[#4A453E]/05 rounded-[32px] p-8 shadow-sm">
            <div className="flex items-center gap-3 mb-8">
              <div className="size-10 rounded-2xl bg-[#FF8A65]/10 flex items-center justify-center"><span className="material-symbols-outlined text-[#FF8A65]">flag</span></div>
              <h3 className="font-serif-brand font-bold text-xl text-[#4A453E]">目标与进度</h3>
            </div>
            <div className="space-y-8">
              <div>
                <label className="block text-[10px] font-bold text-[#4A453E]/40 uppercase tracking-widest px-1 mb-4">主要目标</label>
                <div className="grid grid-cols-2 gap-2">
                  {['减脂', '增肌', '日常健康', '巅峰体能'].map((goal) => (
                    <label key={goal} className="group p-4 bg-[#F7F3E9]/30 border border-transparent rounded-[24px] cursor-pointer transition-all hover:bg-white hover:border-[#FF8A65]/20 has-[:checked]:border-[#FF8A65] has-[:checked]:bg-white overflow-hidden">
                      <input type="radio" name="primary-goal" className="sr-only" checked={profile.goal === goal} onChange={() => updateProfile('goal', goal)} />
                      <span className="text-sm font-bold text-[#4A453E] group-has-[:checked]:text-[#FF8A65] truncate">{goal}</span>
                    </label>
                  ))}
                </div>
              </div>
              <div className="grid grid-cols-1 sm:grid-cols-2 gap-6">
                <div>
                  <label className="block text-[10px] font-bold text-[#4A453E]/40 uppercase tracking-widest px-1 mb-4">每日热量目标</label>
                  <div className="relative group">
                    <input type="number" value={profile.kcalTarget} onChange={(e) => updateProfile('kcalTarget', e.target.value)} className="w-full bg-[#F7F3E9]/30 border border-[#4A453E]/05 rounded-[18px] px-4 py-3 font-bold text-xl text-[#4A453E] focus:ring-2 focus:ring-[#FF8A65]/20 focus:bg-white outline-none transition-all" />
                    <span className="absolute right-4 top-1/2 -translate-y-1/2 text-[9px] font-bold text-[#4A453E]/20 uppercase">kcal</span>
                  </div>
                </div>
              </div>
            </div>
          </div>

          <div className="bg-white border border-[#4A453E]/05 rounded-[32px] p-8 shadow-sm">
            <div className="flex items-center gap-3 mb-8">
              <div className="size-10 rounded-2xl bg-[#81C784]/10 flex items-center justify-center"><span className="material-symbols-outlined text-[#81C784]">restaurant</span></div>
              <h3 className="font-serif-brand font-bold text-xl text-[#4A453E]">饮食习惯</h3>
            </div>
            <div className="space-y-8">
              <div>
                <label className="block text-[10px] font-bold text-[#4A453E]/40 uppercase tracking-widest px-1 mb-4">饮食偏好</label>
                <div className="grid grid-cols-1 sm:grid-cols-2 gap-2">
                  {[
                    { l: '均衡饮食', i: 'nutrition' },
                    { l: '高蛋白饮食', i: 'fitness_center' },
                    { l: '低碳饮食', i: 'grain' },
                    { l: '素食', i: 'eco' }
                  ].map((style) => (
                    <label key={style.l} className="group flex items-center gap-3 p-4 bg-[#F7F3E9]/30 border border-transparent rounded-[24px] cursor-pointer transition-all hover:bg-white hover:border-[#81C784]/20 has-[:checked]:border-[#81C784] has-[:checked]:bg-white overflow-hidden min-h-[64px]">
                      <input type="radio" name="diet-style" className="sr-only" checked={profile.dietStyle === style.l} onChange={() => updateProfile('dietStyle', style.l)} />
                      <span className="material-symbols-outlined text-[#4A453E]/20 group-has-[:checked]:text-[#81C784] transition-colors shrink-0 w-6 flex justify-center">{style.i}</span>
                      <span className="text-sm font-bold text-[#4A453E]/70 group-has-[:checked]:text-[#4A453E] truncate">{style.l}</span>
                    </label>
                  ))}
                </div>
              </div>
              <div>
                <label className="block text-[10px] font-bold text-[#4A453E]/40 uppercase tracking-widest px-1 mb-4">过敏原及避讳食物</label>
                <div className="flex flex-wrap gap-2">
                  {['坚果', '乳制品', '海鲜', '麸质', '大豆', '甲壳类'].map((allergy) => (
                    <label key={allergy} className="group relative flex items-center gap-2 px-4 py-2 bg-[#F7F3E9]/30 border border-transparent rounded-full cursor-pointer transition-all hover:bg-white hover:border-[#4A453E]/10 has-[:checked]:bg-[#4A453E] has-[:checked]:text-white overflow-hidden">
                      <input type="checkbox" className="sr-only" checked={profile.allergies.includes(allergy)} onChange={() => toggleAllergy(allergy)} />
                      <span className={`text-xs font-bold transition-colors truncate ${profile.allergies.includes(allergy) ? 'text-white' : 'text-[#4A453E]/60'}`}>{allergy}</span>
                      {profile.allergies.includes(allergy) && <span className="material-symbols-outlined text-sm font-bold text-white shrink-0">close</span>}
                    </label>
                  ))}
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>

      <div className="bg-[#F7F3E9]/40 border border-[#4A453E]/05 rounded-[32px] p-8 text-center max-w-3xl mx-auto mb-20">
        <h5 className="text-[11px] font-bold text-[#4A453E]/60 uppercase tracking-widest mb-3 flex items-center justify-center gap-2">
          <span className="material-symbols-outlined text-base">info</span> 重要提示
        </h5>
        <p className="text-xs text-[#4A453E]/50 leading-relaxed font-medium">
          Food Pilot 是一款生活方式和健康工具。提供的估算值和建议基于视觉分析和一般营养数据。 
          本信息不应被视为医疗建议、诊断或治疗方案。在制定个性化医疗或营养方案之前，请务必咨询合格的医疗专业人员或注册营养师。
        </p>
      </div>
    </div>
  );
};