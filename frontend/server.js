const express = require('express');
const path = require('path');
const axios = require('axios');
const bodyParser = require('body-parser');
const cors = require('cors');
const session = require('express-session');
const expressLayouts = require('express-ejs-layouts');

const app = express();
const PORT = process.env.PORT || 3000;
const FLASK_API = process.env.FLASK_API || 'http://localhost:5001/api';

app.use(cors());
app.use(bodyParser.json());
app.use(bodyParser.urlencoded({ extended: true }));
app.use(express.static(path.join(__dirname, 'public')));
app.set('view engine', 'ejs');
app.set('views', path.join(__dirname, 'views'));
app.set('layout', 'layout');
app.use(expressLayouts);

app.use(session({
  secret: process.env.SESSION_SECRET || require('crypto').randomBytes(32).toString('hex'),
  resave: false,
  saveUninitialized: false,
  cookie: { maxAge: 8 * 60 * 60 * 1000 }
}));

// Make logged-in user available in all views (including layout)
app.use((req, res, next) => {
  res.locals.user = req.session.user || null;
  next();
});

// Clinic profile (DB settings) available in all views, refreshed every minute
let clinicCache = { ts: 0, data: null };
async function clinicSettings() {
  if (Date.now() - clinicCache.ts < 60000 && clinicCache.data) return clinicCache.data;
  try {
    const { data } = await api.get('/settings');
    clinicCache = { ts: Date.now(), data };
    return data;
  } catch (err) {
    return clinicCache.data || {};
  }
}
app.use(async (req, res, next) => {
  res.locals.clinic = await clinicSettings();
  next();
});

function requireLogin(req, res, next) {
  if (!req.session.user) return res.redirect('/login');
  next();
}

// Public auth routes
app.get('/login', (req, res) => {
  if (req.session.user) return res.redirect('/dashboard');
  res.render('login', { error: null, layout: false });
});

app.post('/login', async (req, res) => {
  try {
    const { data } = await apiFor(req).post('/auth/login', {
      username: req.body.username,
      password: req.body.password
    });
    req.session.user = data;
    res.redirect('/dashboard');
  } catch (err) {
    const msg = (err.response && err.response.data && err.response.data.error)
      || 'Login failed. Please try again.';
    res.status(401).render('login', { error: msg, layout: false });
  }
});

app.get('/logout', (req, res) => {
  req.session.destroy(() => res.redirect('/login'));
});

// Everything below requires login
app.use(['/dashboard', '/patients', '/doctors', '/treatments', '/appointments'], requireLogin);

// Master data is admin-only; staff keep Patients, Doctors and Appointments
app.use(['/treatments', '/masters', '/users'], requireAdmin);

const api = axios.create({ baseURL: FLASK_API, timeout: 5000, headers: { 'X-API-Key': process.env.FLASK_API_KEY || 'dev-key' } });

// Per-request client that also identifies the actor for the backend audit trail
function apiFor(req) {
  const username = (req.session && req.session.user && req.session.user.username) || 'anonymous';
  return axios.create({ baseURL: FLASK_API, timeout: 5000, headers: { 'X-API-Key': process.env.FLASK_API_KEY || 'dev-key', 'X-User': username } });
}

app.get('/', (req, res) => res.redirect('/dashboard'));

app.get('/dashboard', async (req, res) => {
  try {
    const [patients, doctors, treatments, appointments] = await Promise.all([
      api.get('/patients').catch(() => ({ data: [] })),
      api.get('/doctors').catch(() => ({ data: [] })),
      api.get('/treatments').catch(() => ({ data: [] })),
      api.get('/appointments').catch(() => ({ data: [] }))
    ]);
    res.render('dashboard', {
      patients: patients.data,
      doctors: doctors.data,
      treatments: treatments.data,
      appointments: appointments.data
    });
  } catch (err) {
    res.render('dashboard', { patients: [], doctors: [], treatments: [], appointments: [] });
  }
});

app.get('/patients', async (req, res) => {
  try {
    const { data } = await api.get('/patients');
    res.render('patients', { patients: data });
  } catch (err) {
    res.render('patients', { patients: [] });
  }
});

app.get('/patients/new', async (req, res) => {
  const [genders, blood_groups] = await Promise.all([lookupValues('gender'), lookupValues('blood_group')]);
  res.render('patient_form', { patient: null, genders, blood_groups });
});
app.get('/patients/:id/edit', async (req, res) => {
  try {
    const { data } = await api.get(`/patients/${req.params.id}`);
    const [genders, blood_groups] = await Promise.all([lookupValues('gender'), lookupValues('blood_group')]);
    res.render('patient_form', { patient: data, genders, blood_groups });
  } catch (err) {
    res.redirect('/patients');
  }
});

app.post('/patients', async (req, res) => {
  try {
    await apiFor(req).post('/patients', req.body);
    res.redirect('/patients');
  } catch (err) {
    res.status(500).send('Error creating patient');
  }
});

app.post('/patients/:id', async (req, res) => {
  try {
    await apiFor(req).put(`/patients/${req.params.id}`, req.body);
    res.redirect('/patients');
  } catch (err) {
    res.status(500).send('Error updating patient');
  }
});

app.post('/patients/:id/delete', async (req, res) => {
  try {
    await apiFor(req).delete(`/patients/${req.params.id}`);
    res.redirect('/patients');
  } catch (err) {
    res.status(500).send('Error deleting patient');
  }
});

app.get('/doctors', async (req, res) => {
  try {
    const { data } = await api.get('/doctors');
    res.render('doctors', { doctors: data });
  } catch (err) {
    res.render('doctors', { doctors: [] });
  }
});

app.get('/doctors/new', async (req, res) => {
  const specializations = await lookupValues('specialization');
  res.render('doctor_form', { doctor: null, specializations });
});
app.get('/doctors/:id/edit', async (req, res) => {
  try {
    const { data } = await api.get(`/doctors/${req.params.id}`);
    const specializations = await lookupValues('specialization');
    res.render('doctor_form', { doctor: data, specializations });
  } catch (err) {
    res.redirect('/doctors');
  }
});

app.post('/doctors', async (req, res) => {
  try {
    await apiFor(req).post('/doctors', req.body);
    res.redirect('/doctors');
  } catch (err) {
    res.status(500).send('Error creating doctor');
  }
});

app.post('/doctors/:id', async (req, res) => {
  try {
    await apiFor(req).put(`/doctors/${req.params.id}`, req.body);
    res.redirect('/doctors');
  } catch (err) {
    res.status(500).send('Error updating doctor');
  }
});

app.post('/doctors/:id/delete', async (req, res) => {
  try {
    await apiFor(req).delete(`/doctors/${req.params.id}`);
    res.redirect('/doctors');
  } catch (err) {
    res.status(500).send('Error deleting doctor');
  }
});

app.get('/treatments', async (req, res) => {
  try {
    const { data } = await api.get('/treatments');
    res.render('treatments', { treatments: data });
  } catch (err) {
    res.render('treatments', { treatments: [] });
  }
});

app.get('/treatments/new', async (req, res) => {
  const categories = await lookupValues('treatment_category');
  res.render('treatment_form', { treatment: null, categories });
});
app.get('/treatments/:id/edit', async (req, res) => {
  try {
    const { data } = await api.get(`/treatments/${req.params.id}`);
    const categories = await lookupValues('treatment_category');
    res.render('treatment_form', { treatment: data, categories });
  } catch (err) {
    res.redirect('/treatments');
  }
});

app.post('/treatments', async (req, res) => {
  try {
    await apiFor(req).post('/treatments', req.body);
    res.redirect('/treatments');
  } catch (err) {
    res.status(500).send('Error creating treatment');
  }
});

app.post('/treatments/:id', async (req, res) => {
  try {
    await apiFor(req).put(`/treatments/${req.params.id}`, req.body);
    res.redirect('/treatments');
  } catch (err) {
    res.status(500).send('Error updating treatment');
  }
});

app.post('/treatments/:id/delete', async (req, res) => {
  try {
    await apiFor(req).delete(`/treatments/${req.params.id}`);
    res.redirect('/treatments');
  } catch (err) {
    res.status(500).send('Error deleting treatment');
  }
});

app.get('/appointments', async (req, res) => {
  try {
    const [appointments, patients, doctors, treatments] = await Promise.all([
      api.get('/appointments').catch(() => ({ data: [] })),
      api.get('/patients').catch(() => ({ data: [] })),
      api.get('/doctors').catch(() => ({ data: [] })),
      api.get('/treatments').catch(() => ({ data: [] }))
    ]);
    res.render('appointments', {
      appointments: appointments.data,
      patients: patients.data,
      doctors: doctors.data,
      treatments: treatments.data
    });
  } catch (err) {
    res.render('appointments', { appointments: [], patients: [], doctors: [], treatments: [] });
  }
});

app.get('/appointments/new', async (req, res) => {
  try {
    const [patients, doctors, treatments, statuses] = await Promise.all([
      api.get('/patients').catch(() => ({ data: [] })),
      api.get('/doctors').catch(() => ({ data: [] })),
      api.get('/treatments').catch(() => ({ data: [] })),
      lookupValues('appointment_status')
    ]);
    res.render('appointment_form', { appointment: null, patients: patients.data, doctors: doctors.data, treatments: treatments.data, statuses });
  } catch (err) {
    res.render('appointment_form', { appointment: null, patients: [], doctors: [], treatments: [], statuses: [] });
  }
});

app.get('/appointments/:id/edit', async (req, res) => {
  try {
    const [appointment, patients, doctors, treatments, statuses] = await Promise.all([
      api.get(`/appointments/${req.params.id}`),
      api.get('/patients').catch(() => ({ data: [] })),
      api.get('/doctors').catch(() => ({ data: [] })),
      api.get('/treatments').catch(() => ({ data: [] })),
      lookupValues('appointment_status')
    ]);
    res.render('appointment_form', { appointment: appointment.data, patients: patients.data, doctors: doctors.data, treatments: treatments.data, statuses });
  } catch (err) {
    res.redirect('/appointments');
  }
});

app.post('/appointments', async (req, res) => {
  try {
    await apiFor(req).post('/appointments', req.body);
    res.redirect('/appointments');
  } catch (err) {
    res.status(500).send('Error creating appointment');
  }
});

app.post('/appointments/:id', async (req, res) => {
  try {
    await apiFor(req).put(`/appointments/${req.params.id}`, req.body);
    res.redirect('/appointments');
  } catch (err) {
    res.status(500).send('Error updating appointment');
  }
});

app.post('/appointments/:id/delete', async (req, res) => {
  try {
    await apiFor(req).delete(`/appointments/${req.params.id}`);
    res.redirect('/appointments');
  } catch (err) {
    res.status(500).send('Error deleting appointment');
  }
});

// Fetch active values of a master-data (lookup) type from the Flask API
async function lookupValues(type) {
  try {
    const { data } = await api.get('/lookups', { params: { type } });
    return data.filter(l => l.is_active).map(l => l.value);
  } catch (err) {
    return [];
  }
}

function requireAdmin(req, res, next) {
  if (!req.session.user) return res.redirect('/login');
  if (req.session.user.role !== 'admin') return res.status(403).send('Admins only');
  next();
}

// URL slug -> lookup type for dedicated master forms.
// Display metadata (label, icon, description) comes from the /api/lookup-types table.
const MASTER_SECTION_TYPES = {
  specializations: 'specialization',
  categories: 'treatment_category',
  statuses: 'appointment_status'
};

async function lookupTypes() {
  try {
    const { data } = await api.get('/lookup-types');
    return data;
  } catch (err) {
    return [];
  }
}

function sectionKeyFor(lookupType) {
  return Object.keys(MASTER_SECTION_TYPES).find(k => MASTER_SECTION_TYPES[k] === lookupType);
}

app.get('/masters', requireAdmin, async (req, res) => {
  try {
    const [{ data: lookups }, types] = await Promise.all([api.get('/lookups'), lookupTypes()]);
    const groups = {};
    lookups.forEach(l => { (groups[l.type] = groups[l.type] || []).push(l); });
    renderMasters(res, groups, types, null);
  } catch (err) {
    renderMasters(res, {}, [], 'Could not load master data');
  }
});

function renderMasters(res, groups, types, error) {
  const sections = types
    .filter(t => t.has_form && sectionKeyFor(t.type))
    .map(t => ({ key: sectionKeyFor(t.type), ...t }));
  const hubTypes = types.filter(t => !t.has_form);
  res.render('masters', { groups, sections, hubTypes, error });
}

// Dedicated form for one master-data type: /masters/specializations, /masters/categories, /masters/statuses
app.get('/masters/:section', requireAdmin, async (req, res, next) => {
  const lookupType = MASTER_SECTION_TYPES[req.params.section];
  if (!lookupType) return next();
  const section = await lookupSectionMeta(req.params.section, lookupType);
  try {
    const { data } = await api.get('/lookups', { params: { type: lookupType } });
    res.render('master_type', { key: req.params.section, section, values: data, error: null });
  } catch (err) {
    res.render('master_type', { key: req.params.section, section, values: [], error: 'Could not load values' });
  }
});

async function lookupSectionMeta(key, lookupType) {
  const types = await lookupTypes();
  return types.find(t => t.type === lookupType)
    || { type: lookupType, label: key, icon: 'bi-tags', description: '', placeholder: '' };
}

app.post('/masters/:section', requireAdmin, async (req, res, next) => {
  const lookupType = MASTER_SECTION_TYPES[req.params.section];
  if (!lookupType) return next();
  try {
    await apiFor(req).post('/lookups', { type: lookupType, value: req.body.value });
    res.redirect(`/masters/${req.params.section}`);
  } catch (err) {
    const { data } = await api.get('/lookups', { params: { type: lookupType } }).catch(() => ({ data: [] }));
    const section = await lookupSectionMeta(req.params.section, lookupType);
    const msg = (err.response && err.response.data && err.response.data.error) || 'Error adding value';
    res.status(400).render('master_type', { key: req.params.section, section, values: data, error: msg });
  }
});

app.post('/masters', requireAdmin, async (req, res) => {
  try {
    await apiFor(req).post('/lookups', { type: req.body.type, value: req.body.value });
    res.redirect('/masters');
  } catch (err) {
    res.status(500).send('Error adding value');
  }
});

app.post('/masters/:id/toggle', requireAdmin, async (req, res) => {
  try {
    const { data } = await api.get(`/lookups/${req.params.id}`);
    await apiFor(req).put(`/lookups/${req.params.id}`, { is_active: !data.is_active });
    res.redirect(req.body.returnTo || '/masters');
  } catch (err) {
    res.status(500).send('Error updating value');
  }
});

app.post('/masters/:id/delete', requireAdmin, async (req, res) => {
  try {
    await apiFor(req).delete(`/lookups/${req.params.id}`);
    res.redirect(req.body.returnTo || '/masters');
  } catch (err) {
    res.status(500).send('Error deleting value');
  }
});

// User management (admin only)
app.get('/users', requireAdmin, async (req, res) => {
  try {
    const { data } = await api.get('/users');
    res.render('users', { users: data, error: req.query.error || null });
  } catch (err) {
    res.render('users', { users: [], error: 'Could not load users' });
  }
});

app.get('/users/new', requireAdmin, async (req, res) => {
  const roles = await lookupValues('user_role');
  res.render('user_form', { targetUser: null, roles, error: null });
});

app.get('/users/:id/edit', requireAdmin, async (req, res) => {
  try {
    const { data } = await api.get(`/users/${req.params.id}`);
    const roles = await lookupValues('user_role');
    res.render('user_form', { targetUser: data, roles, error: null });
  } catch (err) {
    res.redirect('/users');
  }
});

app.post('/users', requireAdmin, async (req, res) => {
  try {
    await apiFor(req).post('/auth/register', req.body);
    res.redirect('/users');
  } catch (err) {
    const msg = (err.response && err.response.data && err.response.data.error)
      || 'Error creating user';
    const roles = await lookupValues('user_role');
    res.status(400).render('user_form', { targetUser: null, roles, error: msg });
  }
});

app.post('/users/:id', requireAdmin, async (req, res) => {
  try {
    const payload = { username: req.body.username, role: req.body.role };
    if (req.body.password) payload.password = req.body.password;
    const { data } = await apiFor(req).put(`/users/${req.params.id}`, payload);
    if (req.session.user && req.session.user.id === data.id) {
      req.session.user = { ...req.session.user, username: data.username, role: data.role };
    }
    res.redirect('/users');
  } catch (err) {
    const msg = (err.response && err.response.data && err.response.data.error)
      || 'Error updating user';
    const roles = await lookupValues('user_role');
    res.status(400).render('user_form', {
      targetUser: { id: req.params.id, username: req.body.username, role: req.body.role },
      roles, error: msg
    });
  }
});

app.post('/users/:id/delete', requireAdmin, async (req, res) => {
  if (req.session.user && String(req.session.user.id) === String(req.params.id)) {
    return res.redirect('/users?error=' + encodeURIComponent('You cannot delete your own account'));
  }
  try {
    await apiFor(req).delete(`/users/${req.params.id}`);
    res.redirect('/users');
  } catch (err) {
    const msg = (err.response && err.response.data && err.response.data.error)
      || 'Error deleting user';
    res.redirect('/users?error=' + encodeURIComponent(msg));
  }
});

// Billing (staff + admin)
app.get('/bills', requireLogin, async (req, res) => {
  try {
    const [{ data: bills }, { data: appointments }] = await Promise.all([
      api.get('/bills'),
      api.get('/appointments').catch(() => ({ data: [] }))
    ]);
    const billedIds = new Set(bills.map(b => b.appointment_id));
    res.render('bills', {
      bills,
      unbilled: appointments.filter(a => !billedIds.has(a.id)),
      error: req.query.error || null
    });
  } catch (err) {
    res.render('bills', { bills: [], unbilled: [], error: 'Could not load bills' });
  }
});

app.post('/bills/generate', requireLogin, async (req, res) => {
  try {
    const { data } = await apiFor(req).post('/bills', { appointment_id: req.body.appointment_id });
    res.redirect(`/bills/${data.id}`);
  } catch (err) {
    const msg = (err.response && err.response.data && err.response.data.error)
      || 'Error generating bill';
    res.redirect('/bills?error=' + encodeURIComponent(msg));
  }
});

app.get('/bills/:id', requireLogin, async (req, res) => {
  try {
    const { data } = await api.get(`/bills/${req.params.id}`);
    const methods = await lookupValues('payment_method');
    res.render('invoice', { bill: data, methods, error: null });
  } catch (err) {
    res.redirect('/bills');
  }
});

app.post('/bills/:id/pay', requireLogin, async (req, res) => {
  try {
    await apiFor(req).post(`/bills/${req.params.id}/payments`, req.body);
    res.redirect(`/bills/${req.params.id}`);
  } catch (err) {
    const msg = (err.response && err.response.data && err.response.data.error)
      || 'Error recording payment';
    try {
      const { data } = await api.get(`/bills/${req.params.id}`);
      const methods = await lookupValues('payment_method');
      res.status(400).render('invoice', { bill: data, methods, error: msg });
    } catch (e) {
      res.redirect('/bills');
    }
  }
});

// Reports (admin only)
app.get('/reports', requireAdmin, async (req, res) => {
  const params = {};
  if (req.query.from) params.from = req.query.from;
  if (req.query.to) params.to = req.query.to;
  try {
    const [revenue, appts] = await Promise.all([
      api.get('/reports/revenue', { params }).catch(() => ({ data: null })),
      api.get('/reports/appointments', { params }).catch(() => ({ data: null }))
    ]);
    res.render('reports', {
      revenue: revenue.data, appts: appts.data,
      from: req.query.from || '', to: req.query.to || ''
    });
  } catch (err) {
    res.render('reports', { revenue: null, appts: null, from: '', to: '' });
  }
});

app.get('/reports/:name.csv', requireAdmin, async (req, res, next) => {
  if (!['revenue', 'appointments'].includes(req.params.name)) return next();
  try {
    const r = await apiFor(req).get(`/reports/${req.params.name}.csv`,
      { params: req.query, responseType: 'arraybuffer' });
    res.set('Content-Type', 'text/csv');
    res.set('Content-Disposition', `attachment; filename=${req.params.name}.csv`);
    res.send(Buffer.from(r.data));
  } catch (err) {
    res.status(500).send('Error exporting report');
  }
});

// Audit trail (admin only)
app.get('/audit', requireAdmin, async (req, res) => {
  const params = { limit: 200 };
  if (req.query.entity) params.entity = req.query.entity;
  try {
    const { data } = await api.get('/audit', { params });
    res.render('audit', { logs: data, entity: req.query.entity || '' });
  } catch (err) {
    res.render('audit', { logs: [], entity: '' });
  }
});

// Clinic settings (admin only)
app.get('/settings', requireAdmin, async (req, res) => {
  try {
    const { data } = await api.get('/settings');
    res.render('settings', { settings: data, saved: req.query.saved || null });
  } catch (err) {
    res.render('settings', { settings: {}, saved: null });
  }
});

app.post('/settings', requireAdmin, async (req, res) => {
  try {
    await apiFor(req).put('/settings', req.body);
    clinicCache.ts = 0;
    res.redirect('/settings?saved=1');
  } catch (err) {
    res.status(500).send('Error saving settings');
  }
});

app.listen(PORT, () => console.log(`Frontend running on http://localhost:${PORT}`));