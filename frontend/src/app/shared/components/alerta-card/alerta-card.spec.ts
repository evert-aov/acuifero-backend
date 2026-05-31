import { ComponentFixture, TestBed } from '@angular/core/testing';

import { AlertaCard } from './alerta-card';

describe('AlertaCard', () => {
  let component: AlertaCard;
  let fixture: ComponentFixture<AlertaCard>;

  beforeEach(async () => {
    await TestBed.configureTestingModule({
      imports: [AlertaCard],
    }).compileComponents();

    fixture = TestBed.createComponent(AlertaCard);
    component = fixture.componentInstance;
    await fixture.whenStable();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
