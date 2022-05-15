import { ComponentFixture, TestBed } from '@angular/core/testing';

import { DealermachineComponent } from './dealermachine.component';

describe('DealermachineComponent', () => {
  let component: DealermachineComponent;
  let fixture: ComponentFixture<DealermachineComponent>;

  beforeEach(async () => {
    await TestBed.configureTestingModule({
      declarations: [ DealermachineComponent ]
    })
    .compileComponents();
  });

  beforeEach(() => {
    fixture = TestBed.createComponent(DealermachineComponent);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
