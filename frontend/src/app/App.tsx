
import React, { useState, useEffect } from 'react';
import { Header } from './components/Header';
import { Workspace } from './pages/Workspace';
import { Explorer } from './pages/Explorer';
import { Profile } from './pages/Profile';
import { AppView, ChatSession, FoodLogEntry, UserProfile } from './types';

const MOCK_USER_SESSIONS: ChatSession[] = [
  {
    id: '8291',
    title: '地中海风格午餐',
    icon: 'restaurant',
    timestamp: new Date(),
    messages: [
      {
        role: 'user',
        content: '请预估一份鸡肉沙拉（含牛油果和一个小苹果）的热量。',
        time: '下午 12:45'
      },
      {
        role: 'assistant',
        isResult: true,
        title: '分析完成',
        confidence: '高准确度',
        description: "根据标准份量，这顿餐食是瘦肉蛋白、健康脂肪和纤维的均衡组合。",
        items: [
          { name: '烤鸡胸肉', portion: '150g', energy: '248 kcal' },
          { name: '新鲜混合生菜', portion: '2 杯', energy: '20 kcal' },
          { name: '哈斯牛油果', portion: '0.5 个', energy: '160 kcal' },
          { name: '嘎啦苹果', portion: '1 个（小）', energy: '75 kcal' }
        ],
        total: '503 kcal',
        time: '下午 12:46'
      }
    ]
  }
];

const MOCK_USER_LOG: FoodLogEntry[] = [
  {
    id: '1',
    name: '香草鸡肉能量碗',
    description: '烤鸡胸肉配藜麦、羽衣甘蓝和柠檬芝麻酱。',
    calories: '480',
    date: '今天',
    time: '下午 1:15',
    image: 'https://images.unsplash.com/photo-1546069901-ba9599a7e63c?auto=format&fit=crop&q=80&w=400',
    protein: '32g',
    carbs: '45g',
    fat: '18g',
    breakdown: [
      { name: '烤鸡肉', portion: '150g', energy: '248 kcal' },
      { name: '藜麦', portion: '1 杯', energy: '222 kcal' },
      { name: '羽衣甘蓝 & 芝麻酱', portion: '1.5 杯', energy: '10 kcal' }
    ]
  }
];

const DEFAULT_PROFILE: UserProfile = {
  age: '',
  height: '',
  weight: '',
  sex: '不愿透露',
  activityLevel: '久坐',
  exerciseType: '极少',
  goal: '日常健康',
  pace: '适中',
  kcalTarget: '2000',
  dietStyle: '均衡饮食',
  allergies: []
};

const USER_PROFILE: UserProfile = {
  age: '28',
  height: '178',
  weight: '72',
  sex: '男',
  activityLevel: '轻度活动',
  exerciseType: '混合运动',
  goal: '增肌',
  pace: '适中',
  kcalTarget: '2400',
  dietStyle: '高蛋白饮食',
  allergies: ['坚果']
};

const App: React.FC = () => {
  const [currentView, setCurrentView] = useState<AppView>(AppView.WORKSPACE);
  const [isLoggedIn, setIsLoggedIn] = useState(true);
  const [sessions, setSessions] = useState<ChatSession[]>(MOCK_USER_SESSIONS);
  const [foodLog, setFoodLog] = useState<FoodLogEntry[]>(MOCK_USER_LOG);
  const [profile, setProfile] = useState<UserProfile>(USER_PROFILE);

  const handleLogout = () => {
    setIsLoggedIn(false);
    setSessions([]);
    setFoodLog([]);
    setProfile(DEFAULT_PROFILE);
    setCurrentView(AppView.WORKSPACE);
  };

  const handleLogin = () => {
    setIsLoggedIn(true);
    setSessions(MOCK_USER_SESSIONS);
    setFoodLog(MOCK_USER_LOG);
    setProfile(USER_PROFILE);
  };

  const renderView = () => {
    switch (currentView) {
      case AppView.WORKSPACE:
        return <Workspace sessions={sessions} setSessions={setSessions} />;
      case AppView.EXPLORER:
        return <Explorer logEntries={foodLog} />;
      case AppView.PROFILE:
        return <Profile profile={profile} setProfile={setProfile} />;
      default:
        return <Workspace sessions={sessions} setSessions={setSessions} />;
    }
  };

  return (
    <div className="min-h-screen flex flex-col overflow-hidden bg-[#FFFDF5]">
      <Header 
        currentView={currentView} 
        onViewChange={setCurrentView} 
        isLoggedIn={isLoggedIn}
        onLogin={handleLogin}
        onLogout={handleLogout}
      />
      <main className="flex-1 flex overflow-hidden h-[calc(100vh-64px)]">
        {renderView()}
      </main>
    </div>
  );
};

export default App;