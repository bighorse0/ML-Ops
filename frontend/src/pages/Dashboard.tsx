export default function Dashboard() {
  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-3xl font-bold">Dashboard</h1>
        <p className="text-muted-foreground">Welcome to your Feature Store dashboard</p>
      </div>
      
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
        <div className="card">
          <div className="card-content">
            <h3 className="text-lg font-semibold">Total Features</h3>
            <p className="text-3xl font-bold text-primary">156</p>
          </div>
        </div>
        
        <div className="card">
          <div className="card-content">
            <h3 className="text-lg font-semibold">Active Features</h3>
            <p className="text-3xl font-bold text-success">142</p>
          </div>
        </div>
        
        <div className="card">
          <div className="card-content">
            <h3 className="text-lg font-semibold">Alerts</h3>
            <p className="text-3xl font-bold text-warning">3</p>
          </div>
        </div>
        
        <div className="card">
          <div className="card-content">
            <h3 className="text-lg font-semibold">API Calls</h3>
            <p className="text-3xl font-bold text-info">2.4M</p>
          </div>
        </div>
      </div>
    </div>
  )
} 