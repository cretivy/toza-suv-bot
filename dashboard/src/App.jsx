import React, { useState, useEffect } from 'react';
import { 
  BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer,
  LineChart, Line, PieChart, Pie, Cell 
} from 'recharts';
import { Users, Truck, ShoppingCart, DollarSign, Activity } from 'lucide-react';
import { expandWebApp, getTelegramUser } from './utils/telegram';

const COLORS = ['#0088FE', '#00C49F', '#FFBB28', '#FF8042'];

const App = () => {
  const [user, setUser] = useState(null);
  
  useEffect(() => {
    expandWebApp();
    setUser(getTelegramUser());
  }, []);

  const [data, setData] = useState({
    stats: {
      totalOrders: 124,
      revenue: "2,480,000",
      activeDrivers: 3,
      totalCustomers: 45
    },
    ordersTrend: [
      { name: 'Mon', count: 12 },
      { name: 'Tue', count: 19 },
      { name: 'Wed', count: 15 },
      { name: 'Thu', count: 22 },
      { name: 'Fri', count: 30 },
      { name: 'Sat', count: 25 },
      { name: 'Sun', count: 10 },
    ],
    driverStats: [
      { name: 'Haydovchi 1', orders: 45 },
      { name: 'Haydovchi 2', orders: 32 },
      { name: 'Haydovchi 3', orders: 28 },
    ],
    payments: [
      { name: 'Naqd', value: 65 },
      { name: 'Click', value: 35 },
      { name: 'Payme', value: 24 },
    ]
  });

  return (
    <div className="dashboard-container">
      <header>
        <h1 className="gradient-text">
          Toza Suv Admin
        </h1>
        {user && <p className="subtitle">Xush kelibsiz, {user.first_name}!</p>}
        <p className="subtitle">Real-time Dashboard</p>
      </header>

      {/* Stats Grid */}
      <div className="stats-grid">
        <StatCard icon={<ShoppingCart size={20}/>} label="Buyurtmalar" value={data.stats.totalOrders} color="blue" />
        <StatCard icon={<DollarSign size={20}/>} label="Tushum (so'm)" value={data.stats.revenue} color="green" />
        <StatCard icon={<Truck size={20}/>} label="Haydovchilar" value={data.stats.activeDrivers} color="yellow" />
        <StatCard icon={<Users size={20}/>} label="Mijozlar" value={data.stats.totalCustomers} color="purple" />
      </div>

      {/* Charts */}
      <div className="charts-container">
        <div className="chart-section">
          <h2 className="chart-title">
            <Activity size={18} style={{color: '#60a5fa'}} /> Buyurtmalar dinamikasi
          </h2>
          <div style={{height: '250px'}}>
            <ResponsiveContainer width="100%" height="100%">
              <LineChart data={data.ordersTrend}>
                <CartesianGrid strokeDasharray="3 3" stroke="#334155" />
                <XAxis dataKey="name" stroke="#94a3b8" />
                <YAxis stroke="#94a3b8" />
                <Tooltip 
                  contentStyle={{ backgroundColor: '#1e293b', border: 'none', borderRadius: '8px' }}
                  itemStyle={{ color: '#60a5fa' }}
                />
                <Line type="monotone" dataKey="count" stroke="#3b82f6" strokeWidth={3} dot={{r: 6}} />
              </LineChart>
            </ResponsiveContainer>
          </div>
        </div>

        <div className="chart-section">
          <h2 className="chart-title">Haydovchilar samaradorligi</h2>
          <div style={{height: '250px'}}>
            <ResponsiveContainer width="100%" height="100%">
              <BarChart data={data.driverStats}>
                <CartesianGrid strokeDasharray="3 3" stroke="#334155" />
                <XAxis dataKey="name" stroke="#94a3b8" />
                <YAxis stroke="#94a3b8" />
                <Tooltip 
                  contentStyle={{ backgroundColor: '#1e293b', border: 'none', borderRadius: '8px' }}
                />
                <Bar dataKey="orders" fill="#10b981" radius={[4, 4, 0, 0]} />
              </BarChart>
            </ResponsiveContainer>
          </div>
        </div>

        <div className="chart-section">
          <h2 className="chart-title">To'lov turlari</h2>
          <div style={{height: '250px'}}>
            <ResponsiveContainer width="100%" height="100%">
              <PieChart>
                <Pie
                  data={data.payments}
                  cx="50%"
                  cy="50%"
                  innerRadius={60}
                  outerRadius={80}
                  paddingAngle={5}
                  dataKey="value"
                >
                  {data.payments.map((entry, index) => (
                    <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
                  ))}
                </Pie>
                <Tooltip 
                  contentStyle={{ backgroundColor: '#1e293b', border: 'none', borderRadius: '8px' }}
                />
                <Legend verticalAlign="bottom" height={36}/>
              </PieChart>
            </ResponsiveContainer>
          </div>
        </div>
      </div>
      
      <footer>
        Powered by Antigravity AI
      </footer>
    </div>
  );
};

const StatCard = ({ icon, label, value, color }) => {
  return (
    <div className="stat-card">
      <div className={`icon-wrapper icon-${color}`}>
        {icon}
      </div>
      <p className="stat-label">{label}</p>
      <p className="stat-value">{value}</p>
    </div>
  );
};

export default App;
