import { ComponentFixture, TestBed } from '@angular/core/testing';

import { MapaScz } from './mapa-scz';

describe('MapaScz', () => {
  let component: MapaScz;
  let fixture: ComponentFixture<MapaScz>;

  beforeEach(async () => {
    await TestBed.configureTestingModule({
      imports: [MapaScz],
    }).compileComponents();

    fixture = TestBed.createComponent(MapaScz);
    component = fixture.componentInstance;
    await fixture.whenStable();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
