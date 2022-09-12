import { ComponentFixture, TestBed } from '@angular/core/testing';

import { CandymachineComponent } from './candymachine.component';

describe('CandymachineComponent', () => {
  let component: CandymachineComponent;
  let fixture: ComponentFixture<CandymachineComponent>;

  beforeEach(async () => {
    await TestBed.configureTestingModule({
      declarations: [ CandymachineComponent ]
    })
    .compileComponents();
  });

  beforeEach(() => {
    fixture = TestBed.createComponent(CandymachineComponent);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
