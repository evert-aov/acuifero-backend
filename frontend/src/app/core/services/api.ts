import { Injectable } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { environment } from '../../../environments/environment';
import { Municipio, Prediccion, Alerta, Reading } from '../models/municipio.model';

@Injectable({ providedIn: 'root' })
export class Api {
  private base = environment.apiUrl;

  constructor(private http: HttpClient) {}

  getMunicipios()                          { return this.http.get<Municipio[]>(`${this.base}/municipios/`); }
  getMunicipio(id: number)                 { return this.http.get<Municipio>(`${this.base}/municipios/${id}`); }
  getPrediccion(id: number)                { return this.http.get<Prediccion>(`${this.base}/prediccion/${id}`); }
  getAlertas()                             { return this.http.get<Alerta[]>(`${this.base}/alertas/`); }
  getResumenGemini(id: number)             { return this.http.post<{ resumen: string; municipio: string }>(`${this.base}/gemini/resumen`, { municipio_id: id }); }
  getReadings(id: number, days = 90)       { return this.http.get<Reading[]>(`${this.base}/readings/${id}?days=${days}`); }
  getLastReading(id: number)               { return this.http.get<Reading>(`${this.base}/readings/${id}/last`); }
}
