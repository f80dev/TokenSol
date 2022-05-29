import { ComponentFixture, TestBed } from '@angular/core/testing';

import { DbtableComponent } from './dbtable.component';

describe('DbtableComponent', () => {
  let component: DbtableComponent;
  let fixture: ComponentFixture<DbtableComponent>;

  beforeEach(async () => {
    await TestBed.configureTestingModule({
      declarations: [ DbtableComponent ]
    })
    .compileComponents();
  });

  beforeEach(() => {
    fixture = TestBed.createComponent(DbtableComponent);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
