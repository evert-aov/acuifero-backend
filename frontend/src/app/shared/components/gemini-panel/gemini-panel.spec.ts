import { ComponentFixture, TestBed } from '@angular/core/testing';

import { GeminiPanel } from './gemini-panel';

describe('GeminiPanel', () => {
  let component: GeminiPanel;
  let fixture: ComponentFixture<GeminiPanel>;

  beforeEach(async () => {
    await TestBed.configureTestingModule({
      imports: [GeminiPanel],
    }).compileComponents();

    fixture = TestBed.createComponent(GeminiPanel);
    component = fixture.componentInstance;
    await fixture.whenStable();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
