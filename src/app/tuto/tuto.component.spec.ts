import { ComponentFixture, TestBed } from '@angular/core/testing';

import { TutoComponent } from './tuto.component';

describe('TutoComponent', () => {
  let component: TutoComponent;
  let fixture: ComponentFixture<TutoComponent>;

  beforeEach(() => {
    TestBed.configureTestingModule({
      declarations: [TutoComponent]
    });
    fixture = TestBed.createComponent(TutoComponent);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
