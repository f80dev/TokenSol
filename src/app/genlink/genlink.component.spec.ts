import { ComponentFixture, TestBed } from '@angular/core/testing';

import { GenlinkComponent } from './genlink.component';

describe('GenlinkComponent', () => {
  let component: GenlinkComponent;
  let fixture: ComponentFixture<GenlinkComponent>;

  beforeEach(() => {
    TestBed.configureTestingModule({
      declarations: [GenlinkComponent]
    });
    fixture = TestBed.createComponent(GenlinkComponent);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
