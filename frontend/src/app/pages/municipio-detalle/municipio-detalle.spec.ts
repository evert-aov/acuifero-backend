import { ComponentFixture, TestBed } from '@angular/core/testing';

import { MunicipioDetalle } from './municipio-detalle';

describe('MunicipioDetalle', () => {
  let component: MunicipioDetalle;
  let fixture: ComponentFixture<MunicipioDetalle>;

  beforeEach(async () => {
    await TestBed.configureTestingModule({
      imports: [MunicipioDetalle],
    }).compileComponents();

    fixture = TestBed.createComponent(MunicipioDetalle);
    component = fixture.componentInstance;
    await fixture.whenStable();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
