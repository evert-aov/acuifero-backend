import { Routes } from '@angular/router';

export const routes: Routes = [
  { path: '', loadComponent: () => import('./pages/landing/landing').then(m => m.Landing) },
  { path: 'dashboard', loadComponent: () => import('./pages/dashboard/dashboard').then(m => m.Dashboard) },
  { path: 'municipio/:id', loadComponent: () => import('./pages/municipio-detalle/municipio-detalle').then(m => m.MunicipioDetalle) },
  { path: '**', redirectTo: '' }
];
