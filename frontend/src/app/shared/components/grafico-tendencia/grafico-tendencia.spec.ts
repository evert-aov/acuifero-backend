import { ComponentFixture, TestBed } from '@angular/core/testing';

import { GraficoTendencia } from './grafico-tendencia';

describe('GraficoTendencia', () => {
  let component: GraficoTendencia;
  let fixture: ComponentFixture<GraficoTendencia>;

  beforeEach(async () => {
    await TestBed.configureTestingModule({
      imports: [GraficoTendencia],
    }).compileComponents();

    fixture = TestBed.createComponent(GraficoTendencia);
    component = fixture.componentInstance;
    await fixture.whenStable();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
